"""
Quiz Battle Service: session management, scoring, XP integration.
Supports: shuffle (questions/answers), answer streak, accuracy mode.
"""
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from app.models.quiz import QuizSession, QuizParticipant, QuizSessionStatus
from app.models.test import QuestionType
from app.models.gamification import XpSourceType
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import QuizQuestionOut, QuizSessionSettings
from app.services.quiz_scoring import calculate_score, calculate_streak_bonus, calculate_xp
from app.services.quiz_question_loader import (
    ALLOWED_QUESTION_TYPES, load_test, get_sorted_questions,
    load_question, check_answer, get_correct_option_index,
)

logger = logging.getLogger(__name__)


class QuizService:
    # Expose for backward compat (used by selfpaced/short_answer via instance)
    ALLOWED_QUESTION_TYPES = ALLOWED_QUESTION_TYPES

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizRepository(db)

    # ── Join code generation ──

    async def generate_join_code(self) -> str:
        for _ in range(10):
            code = str(random.randint(100000, 999999))
            exists = await self.repo.check_join_code_exists(code)
            if not exists:
                return code
        raise ValueError("Could not generate unique join code")

    # ── Session lifecycle ──

    async def create_session(
        self,
        teacher_id: int,
        school_id: int,
        test_id: Optional[int] = None,
        class_id: Optional[int] = None,
        settings: Optional[QuizSessionSettings] = None,
        question_ids: Optional[list[int]] = None,
        custom_questions: Optional[list[dict]] = None,
    ) -> QuizSession:
        settings_obj = settings or QuizSessionSettings()
        mode = settings_obj.mode

        # Quick question mode: no test needed
        if mode == "quick_question":
            join_code = await self.generate_join_code()
            settings_dict = settings_obj.model_dump()
            session = await self.repo.create_session(
                school_id=school_id, teacher_id=teacher_id, test_id=None,
                class_id=class_id, join_code=join_code, question_count=0,
                settings=settings_dict,
            )
            await self.db.commit()
            logger.info(f"Quick question session {session.id} created with code {join_code}")
            return session

        settings_dict = settings_obj.model_dump()

        # ── Cherry-picked / custom questions mode ──
        if question_ids or custom_questions:
            bank_count = 0
            if question_ids:
                # Validate question_ids exist and are quiz-eligible
                from app.services.quiz_question_loader import _load_questions_by_ids
                bank_questions = await _load_questions_by_ids(self.db, question_ids)
                if len(bank_questions) != len(question_ids):
                    found_ids = {q.id for q in bank_questions}
                    missing = [qid for qid in question_ids if qid not in found_ids]
                    raise ValueError(f"Questions not found: {missing}")
                bank_count = len(bank_questions)
                settings_dict["question_ids"] = question_ids

            custom_count = 0
            if custom_questions:
                # Validate custom questions
                for i, cq in enumerate(custom_questions):
                    if cq["correct_option"] >= len(cq["options"]):
                        raise ValueError(f"Custom question {i+1}: correct_option out of range")
                custom_count = len(custom_questions)
                settings_dict["custom_questions"] = custom_questions

            total_count = bank_count + custom_count
            if total_count == 0:
                raise ValueError("No questions provided")

            if mode == "self_paced":
                settings_dict["scoring_mode"] = "accuracy"

            join_code = await self.generate_join_code()
            session = await self.repo.create_session(
                school_id=school_id, teacher_id=teacher_id, test_id=test_id,
                class_id=class_id, join_code=join_code, question_count=total_count,
                settings=settings_dict,
            )

            if mode == "team":
                from app.services.quiz_team_service import QuizTeamService
                team_service = QuizTeamService(self.db)
                team_count = settings_obj.team_count or 2
                await team_service.create_teams(session.id, school_id, team_count)

            await self.db.commit()
            logger.info(f"Quiz session {session.id} created with code {join_code}, {total_count} questions (bank={bank_count}, custom={custom_count}), mode={mode}")
            return session

        # ── Legacy test_id mode ──
        if not test_id:
            raise ValueError("test_id, question_ids, or custom_questions required")

        test = await load_test(self.db, test_id)
        if not test:
            raise ValueError("Test not found or inactive")

        questions = [
            q for q in test.questions
            if q.question_type in ALLOWED_QUESTION_TYPES and not q.is_deleted
        ]
        if not questions:
            raise ValueError("Test has no eligible questions")

        join_code = await self.generate_join_code()

        if mode == "self_paced":
            settings_dict["scoring_mode"] = "accuracy"

        session = await self.repo.create_session(
            school_id=school_id, teacher_id=teacher_id, test_id=test_id,
            class_id=class_id, join_code=join_code, question_count=len(questions),
            settings=settings_dict,
        )

        if mode == "team":
            from app.services.quiz_team_service import QuizTeamService
            team_service = QuizTeamService(self.db)
            team_count = settings_obj.team_count or 2
            await team_service.create_teams(session.id, school_id, team_count)

        await self.db.commit()
        logger.info(f"Quiz session {session.id} created with code {join_code}, {len(questions)} questions, mode={mode}")
        return session

    async def join_session(self, join_code: str, student_id: int, school_id: int) -> dict:
        # Verify RLS tenant context matches the student's school_id.
        # Under concurrent load, BaseHTTPMiddleware (Starlette) may fail to
        # propagate contextvars to the subtask, leaving app.current_tenant_id
        # at '0' (default).  Tables with a user_id fallback (users, students)
        # still work, but quiz_sessions has only a school_id check — so the
        # SELECT silently returns nothing and we get "Invalid quiz code".
        row = await self.db.execute(
            text("SELECT current_setting('app.current_tenant_id', true)")
        )
        current_tid = row.scalar()
        expected_tid = str(school_id)
        if current_tid != expected_tid:
            logger.warning(
                f"Quiz join: RLS tenant mismatch! "
                f"current_tenant_id='{current_tid}', expected='{expected_tid}' "
                f"(student_id={student_id}). Repairing."
            )
            await self.db.execute(
                text("SELECT set_config('app.current_tenant_id', :tid, false)"),
                {"tid": expected_tid},
            )

        session = await self.repo.get_session_by_join_code(join_code)
        if not session:
            raise ValueError("Invalid quiz code")
        allowed_statuses = [QuizSessionStatus.LOBBY]
        if session.mode == "self_paced":
            allowed_statuses.append(QuizSessionStatus.IN_PROGRESS)
        if session.status not in allowed_statuses:
            raise ValueError("Quiz is not accepting participants")
        if session.school_id != school_id:
            raise ValueError("Quiz belongs to a different school")

        mode = session.mode

        existing = await self.repo.get_participant(session.id, student_id)
        team_info = {}
        if not existing:
            participant = await self.repo.add_participant(session.id, student_id, school_id)
            if mode == "team":
                from app.services.quiz_team_service import QuizTeamService
                team_service = QuizTeamService(self.db)
                team = await team_service.assign_to_team(session.id, participant.id)
                if team:
                    team_info = {"team_id": team.id, "team_name": team.name, "team_color": team.color}
            await self.db.commit()
        else:
            if mode == "team" and existing.team_id:
                from app.repositories.quiz_team_repo import QuizTeamRepository
                team_repo = QuizTeamRepository(self.db)
                team = await team_repo.get_team_by_id(existing.team_id)
                if team:
                    team_info = {"team_id": team.id, "team_name": team.name, "team_color": team.color}

        participant_count = await self.repo.get_participant_count(session.id)
        return {
            "quiz_session_id": session.id,
            "join_code": session.join_code,
            "status": session.status.value if isinstance(session.status, QuizSessionStatus) else session.status,
            "participant_count": participant_count,
            "mode": mode,
            **team_info,
        }

    async def start_session(self, session_id: int, teacher_id: int) -> QuizSession:
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.teacher_id != teacher_id:
            raise ValueError("Not the session owner")
        if session.status != QuizSessionStatus.LOBBY:
            raise ValueError("Session is not in lobby")

        participant_count = await self.repo.get_participant_count(session_id)
        if participant_count == 0:
            raise ValueError("No participants joined")

        now = datetime.now(timezone.utc)
        await self.repo.update_session(session_id, status=QuizSessionStatus.IN_PROGRESS, started_at=now, current_question_index=0)
        await self.db.commit()

        session.status = QuizSessionStatus.IN_PROGRESS
        session.started_at = now
        session.current_question_index = 0
        logger.info(f"Quiz session {session_id} started")
        return session

    async def cancel_session(self, session_id: int, teacher_id: int) -> QuizSession:
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.teacher_id != teacher_id:
            raise ValueError("Not the session owner")
        if session.status in (QuizSessionStatus.FINISHED, QuizSessionStatus.CANCELLED):
            raise ValueError("Session already ended")

        await self.repo.update_session(session_id, status=QuizSessionStatus.CANCELLED, finished_at=datetime.now(timezone.utc))
        await self.db.commit()
        session.status = QuizSessionStatus.CANCELLED
        logger.info(f"Quiz session {session_id} cancelled")
        return session

    # ── Questions ──

    async def get_current_question(self, session_id: int) -> Optional[QuizQuestionOut]:
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            return None
        if session.current_question_index < 0 or session.current_question_index >= session.question_count:
            return None
        return await load_question(self.db, session.test_id, session.current_question_index, session.settings, session.id)

    async def advance_question(self, session_id: int, teacher_id: int) -> Optional[QuizQuestionOut]:
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.teacher_id != teacher_id:
            raise ValueError("Not the session owner")
        if session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session is not in progress")

        new_index = session.current_question_index + 1
        if new_index >= session.question_count:
            return None

        await self.repo.update_session(session_id, current_question_index=new_index)
        await self.db.commit()
        return await load_question(self.db, session.test_id, new_index, session.settings, session.id)

    async def go_to_question(self, session_id: int, teacher_id: int, question_index: int) -> Optional[QuizQuestionOut]:
        """Navigate to an arbitrary question (teacher-paced mode only)."""
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.teacher_id != teacher_id:
            raise ValueError("Not the session owner")
        if session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session is not in progress")
        if session.settings.get("pacing") != "teacher_paced":
            raise ValueError("go_to_question is only available in teacher_paced mode")
        if question_index < 0 or question_index >= session.question_count:
            raise ValueError(f"Question index must be 0-{session.question_count - 1}")

        await self.repo.update_session(session_id, current_question_index=question_index)
        await self.db.commit()
        return await load_question(self.db, session.test_id, question_index, session.settings, session.id)

    # ── Answers ──

    async def submit_answer(
        self,
        session_id: int,
        student_id: int,
        question_index: int,
        selected_option: int,
        answer_time_ms: int,
        text_answer: Optional[str] = None,
        confidence_mode: Optional[str] = None,
    ) -> dict:
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")
        if question_index != session.current_question_index:
            raise ValueError("Wrong question index")

        participant = await self.repo.get_participant(session_id, student_id)
        if not participant:
            raise ValueError("Not a participant")

        # Idempotent check (or re-answer in teacher-paced mode)
        existing = await self.repo.get_answer(participant.id, question_index)
        is_teacher_paced = session.settings.get("pacing") == "teacher_paced"
        if existing:
            if not is_teacher_paced:
                return {
                    "is_correct": existing.is_correct, "score": existing.score,
                    "total_score": participant.total_score, "already_answered": True,
                    "current_streak": participant.current_streak, "max_streak": participant.max_streak,
                }
            old_score = existing.score
            old_correct = existing.is_correct
            await self.repo.reverse_answer_score(participant.id, old_score, old_correct)
            await self.repo.delete_answer(existing.id)

        # Determine correctness
        if text_answer is not None:
            from app.services.quiz_short_answer_service import QuizShortAnswerService
            sa_service = QuizShortAnswerService(self.db)
            is_correct, _method = await sa_service.check_answer(
                session.test_id, question_index, text_answer, session.settings, session.id,
            )
        else:
            is_correct = await check_answer(
                self.db, session.test_id, question_index, selected_option,
                session.settings, session.id,
            )

        # Calculate score (with confidence mode support)
        time_limit = session.settings.get("time_per_question_ms", 30000)
        scoring_mode = session.settings.get("scoring_mode", "speed")
        score = calculate_score(is_correct, answer_time_ms, time_limit, scoring_mode, confidence_mode)

        # Apply power-up effects to score
        powerup_used = None
        powerup_effects = {}
        streak_protected = False
        enable_powerups = (session.settings or {}).get("enable_powerups", False)
        if enable_powerups:
            from app.services.quiz_powerup_service import QuizPowerupService
            powerup_service = QuizPowerupService(self.db)
            powerup = await powerup_service.get_active_powerup(participant.id, question_index)
            if powerup:
                score, powerup_effects = await powerup_service.apply_to_score(
                    powerup.powerup_type, score, is_correct,
                )
                powerup_used = powerup.powerup_type
                streak_protected = powerup_effects.get("streak_protected", False)
                await powerup_service.mark_applied(powerup.id)

        # Save answer
        await self.repo.add_answer(
            quiz_session_id=session_id, participant_id=participant.id,
            school_id=session.school_id, question_index=question_index,
            selected_option=selected_option, is_correct=is_correct,
            answer_time_ms=answer_time_ms, score=score, text_answer=text_answer,
            powerup_used=powerup_used, confidence_mode=confidence_mode,
        )

        # Update score and streak (shield protects streak on wrong answer)
        if streak_protected:
            # Don't reset streak — add score without changing streak
            new_streak = participant.current_streak
            new_max = participant.max_streak
            await self.repo.add_streak_bonus(participant.id, score)  # just adds to total_score
        else:
            new_streak, new_max = await self.repo.update_participant_score(participant.id, score, is_correct)

        streak_bonus = calculate_streak_bonus(new_streak)
        if streak_bonus > 0:
            await self.repo.add_streak_bonus(participant.id, streak_bonus)

        await self.db.commit()

        new_total = (participant.total_score or 0) + score + streak_bonus
        return {
            "is_correct": is_correct, "score": score, "streak_bonus": streak_bonus,
            "total_score": new_total, "current_streak": new_streak, "max_streak": new_max,
            "already_answered": False,
            "powerup_used": powerup_used,
            **powerup_effects,
        }

    # ── Question stats ──

    async def get_question_stats(self, session_id: int, question_index: int) -> dict:
        stats = await self.repo.get_answer_stats(session_id, question_index)
        session = await self.repo.get_session(session_id)
        correct_option = await get_correct_option_index(
            self.db, session.test_id, question_index, session.settings, session.id,
        ) if session else None
        return {"stats": stats, "correct_option": correct_option}

    # ── Finish & XP ──

    async def finish_session(self, session_id: int, teacher_id: int) -> dict:
        session = await self.repo.get_session(session_id)
        if not session:
            raise ValueError("Session not found")
        if session.teacher_id != teacher_id:
            raise ValueError("Not the session owner")
        if session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session is not in progress")

        now = datetime.now(timezone.utc)
        await self.repo.update_session(session_id, status=QuizSessionStatus.FINISHED, finished_at=now)

        participants_data = await self.repo.get_participants_with_names(session_id)
        from app.services.gamification_service import GamificationService
        gamification = GamificationService(self.db)

        total_participants = len(participants_data)
        leaderboard = []
        for rank, data in enumerate(participants_data, 1):
            p = data["participant"]
            xp = calculate_xp(rank, p.correct_answers, session.question_count, total_participants)

            await self.repo.set_participant_rank_and_xp(p.id, rank, xp)

            try:
                await gamification.award_xp(
                    student_id=p.student_id, school_id=p.school_id,
                    amount=xp, source_type=XpSourceType.QUIZ_BATTLE,
                    source_id=session_id,
                    extra_data={"rank": rank, "correct": p.correct_answers, "total": session.question_count},
                )
            except Exception as e:
                logger.error(f"Failed to award XP for participant {p.id}: {e}")

            leaderboard.append({
                "rank": rank, "student_id": p.student_id,
                "student_name": data["student_name"],
                "total_score": p.total_score, "correct_answers": p.correct_answers,
                "max_streak": p.max_streak, "xp_earned": xp,
            })

        await self.db.commit()
        logger.info(f"Quiz session {session_id} finished, {len(leaderboard)} participants")

        return {
            "quiz_session_id": session_id,
            "total_questions": session.question_count,
            "leaderboard": leaderboard,
        }
