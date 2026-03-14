"""
Quiz Battle Service: session management, scoring, XP integration.
Supports: shuffle (questions/answers), answer streak, accuracy mode.
"""
import logging
import random
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.quiz import QuizSession, QuizParticipant, QuizSessionStatus
from app.models.test import Test, Question, QuestionOption, QuestionType
from app.models.gamification import XpSourceType
from app.repositories.quiz_repo import QuizRepository
from app.schemas.quiz import QuizQuestionOut, QuizSessionSettings

logger = logging.getLogger(__name__)

# ── Score / XP constants ──
MAX_QUESTION_SCORE = 1000
XP_PARTICIPATION = 10
XP_PER_CORRECT = 5
XP_RANK_1 = 50
XP_RANK_2 = 30
XP_RANK_3 = 15
XP_PERFECT = 25

# Streak bonus thresholds
STREAK_BONUSES = {2: 100, 3: 200, 4: 300}
STREAK_BONUS_CAP = 500  # 5+ streak


class QuizService:
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
        test_id: int,
        class_id: Optional[int] = None,
        settings: Optional[QuizSessionSettings] = None,
    ) -> QuizSession:
        # Load test with questions
        result = await self.db.execute(
            select(Test)
            .options(selectinload(Test.questions).selectinload(Question.options))
            .where(Test.id == test_id, Test.is_active == True, Test.is_deleted == False)
        )
        test = result.scalar_one_or_none()
        if not test:
            raise ValueError("Test not found or inactive")

        # Filter single-choice questions only
        questions = [
            q for q in test.questions
            if q.question_type == QuestionType.SINGLE_CHOICE and not q.is_deleted
        ]
        if not questions:
            raise ValueError("Test has no single-choice questions")

        join_code = await self.generate_join_code()
        settings_dict = (settings or QuizSessionSettings()).model_dump()

        session = await self.repo.create_session(
            school_id=school_id,
            teacher_id=teacher_id,
            test_id=test_id,
            class_id=class_id,
            join_code=join_code,
            question_count=len(questions),
            settings=settings_dict,
        )
        await self.db.commit()
        await self.db.refresh(session)
        logger.info(f"Quiz session {session.id} created with code {join_code}, {len(questions)} questions")
        return session

    async def join_session(self, join_code: str, student_id: int, school_id: int) -> dict:
        session = await self.repo.get_session_by_join_code(join_code)
        if not session:
            raise ValueError("Invalid quiz code")
        if session.status != QuizSessionStatus.LOBBY:
            raise ValueError("Quiz is not accepting participants")
        if session.school_id != school_id:
            raise ValueError("Quiz belongs to a different school")

        # Idempotent: check if already joined
        existing = await self.repo.get_participant(session.id, student_id)
        if not existing:
            await self.repo.add_participant(session.id, student_id, school_id)
            await self.db.commit()

        participant_count = await self.repo.get_participant_count(session.id)
        return {
            "quiz_session_id": session.id,
            "join_code": session.join_code,
            "status": session.status.value if isinstance(session.status, QuizSessionStatus) else session.status,
            "participant_count": participant_count,
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

    # ── Shuffle helpers ──

    def _get_sorted_questions(self, test: Test) -> list[Question]:
        """Get active single-choice questions sorted by sort_order."""
        return sorted(
            [q for q in test.questions if q.question_type == QuestionType.SINGLE_CHOICE and not q.is_deleted],
            key=lambda q: q.sort_order,
        )

    def _get_question_at_index(self, questions: list[Question], question_index: int, settings: dict, session_id: int) -> Optional[Question]:
        """Get question at logical index, applying question shuffle if enabled."""
        if question_index >= len(questions):
            return None
        if settings.get("shuffle_questions"):
            rng = random.Random(session_id)
            indices = list(range(len(questions)))
            rng.shuffle(indices)
            return questions[indices[question_index]]
        return questions[question_index]

    def _get_shuffled_options(self, question: Question, settings: dict, session_id: int, question_index: int) -> list[QuestionOption]:
        """Get active options, optionally shuffled with deterministic seed."""
        options = sorted(
            [o for o in question.options if not o.is_deleted],
            key=lambda o: o.sort_order,
        )
        if settings.get("shuffle_answers"):
            rng = random.Random(session_id * 10000 + question_index)
            indices = list(range(len(options)))
            rng.shuffle(indices)
            return [options[i] for i in indices]
        return options

    # ── Questions ──

    async def get_current_question(self, session_id: int) -> Optional[QuizQuestionOut]:
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            return None
        if session.current_question_index < 0 or session.current_question_index >= session.question_count:
            return None

        return await self._load_question(session.test_id, session.current_question_index, session.settings, session.id)

    async def _load_question(self, test_id: int, question_index: int, settings: dict, session_id: int) -> Optional[QuizQuestionOut]:
        test = await self._load_test(test_id)
        if not test:
            return None

        questions = self._get_sorted_questions(test)
        q = self._get_question_at_index(questions, question_index, settings, session_id)
        if not q:
            return None

        options = self._get_shuffled_options(q, settings, session_id, question_index)
        time_limit = settings.get("time_per_question_ms", 30000)

        return QuizQuestionOut(
            index=question_index,
            text=q.question_text,
            options=[o.option_text for o in options],
            time_limit_ms=time_limit,
            image_url=None,
        )

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
            return None  # Signal to finish

        await self.repo.update_session(session_id, current_question_index=new_index)
        await self.db.commit()
        return await self._load_question(session.test_id, new_index, session.settings, session.id)

    # ── Answers ──

    async def submit_answer(
        self,
        session_id: int,
        student_id: int,
        question_index: int,
        selected_option: int,
        answer_time_ms: int,
    ) -> dict:
        session = await self.repo.get_session(session_id)
        if not session or session.status != QuizSessionStatus.IN_PROGRESS:
            raise ValueError("Session not in progress")
        if question_index != session.current_question_index:
            raise ValueError("Wrong question index")

        participant = await self.repo.get_participant(session_id, student_id)
        if not participant:
            raise ValueError("Not a participant")

        # Idempotent check
        existing = await self.repo.get_answer(participant.id, question_index)
        if existing:
            return {
                "is_correct": existing.is_correct, "score": existing.score,
                "total_score": participant.total_score, "already_answered": True,
                "current_streak": participant.current_streak, "max_streak": participant.max_streak,
            }

        # Determine correctness (handles shuffle mapping)
        is_correct = await self._check_answer(
            session.test_id, question_index, selected_option,
            session.settings, session.id,
        )

        # Calculate score (speed or accuracy mode)
        time_limit = session.settings.get("time_per_question_ms", 30000)
        scoring_mode = session.settings.get("scoring_mode", "speed")
        score = self._calculate_score(is_correct, answer_time_ms, time_limit, scoring_mode)

        # Save answer
        await self.repo.add_answer(
            quiz_session_id=session_id,
            participant_id=participant.id,
            school_id=session.school_id,
            question_index=question_index,
            selected_option=selected_option,
            is_correct=is_correct,
            answer_time_ms=answer_time_ms,
            score=score,
        )

        # Update score and streak atomically
        new_streak, new_max = await self.repo.update_participant_score(participant.id, score, is_correct)

        # Add streak bonus points
        streak_bonus = self._calculate_streak_bonus(new_streak)
        if streak_bonus > 0:
            await self.repo.add_streak_bonus(participant.id, streak_bonus)

        await self.db.commit()

        # Refresh to get updated total
        await self.db.refresh(participant)
        return {
            "is_correct": is_correct,
            "score": score,
            "streak_bonus": streak_bonus,
            "total_score": participant.total_score,
            "current_streak": new_streak,
            "max_streak": new_max,
            "already_answered": False,
        }

    async def _load_test(self, test_id: int) -> Optional[Test]:
        result = await self.db.execute(
            select(Test)
            .options(selectinload(Test.questions).selectinload(Question.options))
            .where(Test.id == test_id)
        )
        return result.scalar_one_or_none()

    async def _check_answer(
        self, test_id: int, question_index: int, selected_option: int,
        settings: dict, session_id: int,
    ) -> bool:
        test = await self._load_test(test_id)
        if not test:
            return False

        questions = self._get_sorted_questions(test)
        q = self._get_question_at_index(questions, question_index, settings, session_id)
        if not q:
            return False

        # Use same shuffle as _load_question so indices match
        options = self._get_shuffled_options(q, settings, session_id, question_index)
        if selected_option < 0 or selected_option >= len(options):
            return False

        return options[selected_option].is_correct

    @staticmethod
    def _calculate_score(is_correct: bool, answer_time_ms: int, time_limit_ms: int, scoring_mode: str = "speed") -> int:
        if not is_correct:
            return 0
        if scoring_mode == "accuracy":
            return MAX_QUESTION_SCORE
        # Speed mode: faster = more points
        time_factor = max(0, 1 - (answer_time_ms / time_limit_ms) / 2)
        return round(MAX_QUESTION_SCORE * time_factor)

    @staticmethod
    def _calculate_streak_bonus(streak: int) -> int:
        if streak < 2:
            return 0
        if streak >= 5:
            return STREAK_BONUS_CAP
        return STREAK_BONUSES.get(streak, 0)

    # ── Question stats ──

    async def get_question_stats(self, session_id: int, question_index: int) -> dict:
        stats = await self.repo.get_answer_stats(session_id, question_index)
        session = await self.repo.get_session(session_id)
        correct_option = await self._get_correct_option_index(
            session.test_id, question_index, session.settings, session.id,
        ) if session else None
        return {"stats": stats, "correct_option": correct_option}

    async def _get_correct_option_index(
        self, test_id: int, question_index: int,
        settings: dict, session_id: int,
    ) -> Optional[int]:
        test = await self._load_test(test_id)
        if not test:
            return None

        questions = self._get_sorted_questions(test)
        q = self._get_question_at_index(questions, question_index, settings, session_id)
        if not q:
            return None

        options = self._get_shuffled_options(q, settings, session_id, question_index)
        for i, o in enumerate(options):
            if o.is_correct:
                return i
        return None

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

        # Calculate ranks and award XP
        participants_data = await self.repo.get_participants_with_names(session_id)
        # Already sorted by total_score DESC
        from app.services.gamification_service import GamificationService
        gamification = GamificationService(self.db)

        leaderboard = []
        for rank, data in enumerate(participants_data, 1):
            p = data["participant"]
            xp = self._calculate_xp(rank, p.correct_answers, session.question_count)

            await self.repo.set_participant_rank_and_xp(p.id, rank, xp)

            # Award XP via gamification service
            try:
                await gamification.award_xp(
                    student_id=p.student_id,
                    school_id=p.school_id,
                    amount=xp,
                    source_type=XpSourceType.QUIZ_BATTLE,
                    source_id=session_id,
                    extra_data={"rank": rank, "correct": p.correct_answers, "total": session.question_count},
                )
            except Exception as e:
                logger.error(f"Failed to award XP for participant {p.id}: {e}")

            leaderboard.append({
                "rank": rank,
                "student_id": p.student_id,
                "student_name": data["student_name"],
                "total_score": p.total_score,
                "correct_answers": p.correct_answers,
                "max_streak": p.max_streak,
                "xp_earned": xp,
            })

        await self.db.commit()
        logger.info(f"Quiz session {session_id} finished, {len(leaderboard)} participants")

        return {
            "quiz_session_id": session_id,
            "total_questions": session.question_count,
            "leaderboard": leaderboard,
        }

    @staticmethod
    def _calculate_xp(rank: int, correct_answers: int, total_questions: int) -> int:
        xp = XP_PARTICIPATION
        xp += correct_answers * XP_PER_CORRECT
        if rank == 1:
            xp += XP_RANK_1
        elif rank == 2:
            xp += XP_RANK_2
        elif rank == 3:
            xp += XP_RANK_3
        if correct_answers == total_questions and total_questions > 0:
            xp += XP_PERFECT
        return xp
