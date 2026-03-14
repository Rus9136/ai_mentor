"""
Repository for Quiz Battle CRUD operations.
"""
import logging
from typing import Optional
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.quiz import QuizSession, QuizParticipant, QuizAnswer, QuizSessionStatus
from app.models.student import Student
from app.models.user import User

logger = logging.getLogger(__name__)


class QuizRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── QuizSession ──

    async def create_session(
        self,
        school_id: int,
        teacher_id: int,
        test_id: int,
        join_code: str,
        question_count: int,
        class_id: Optional[int] = None,
        settings: Optional[dict] = None,
    ) -> QuizSession:
        session = QuizSession(
            school_id=school_id,
            teacher_id=teacher_id,
            test_id=test_id,
            class_id=class_id,
            join_code=join_code,
            question_count=question_count,
            settings=settings or {},
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session(self, session_id: int) -> Optional[QuizSession]:
        result = await self.db.execute(
            select(QuizSession)
            .options(selectinload(QuizSession.participants))
            .where(QuizSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def get_session_by_join_code(self, join_code: str) -> Optional[QuizSession]:
        result = await self.db.execute(
            select(QuizSession)
            .options(selectinload(QuizSession.participants))
            .where(QuizSession.join_code == join_code)
        )
        return result.scalar_one_or_none()

    async def check_join_code_exists(self, join_code: str) -> bool:
        result = await self.db.execute(
            select(func.count()).select_from(QuizSession).where(
                QuizSession.join_code == join_code,
                QuizSession.status.in_([QuizSessionStatus.LOBBY, QuizSessionStatus.IN_PROGRESS]),
            )
        )
        return result.scalar_one() > 0

    async def update_session(self, session_id: int, **kwargs) -> None:
        await self.db.execute(
            update(QuizSession).where(QuizSession.id == session_id).values(**kwargs)
        )

    async def get_sessions_by_teacher(
        self, teacher_id: int, school_id: int, status: Optional[str] = None, limit: int = 50, offset: int = 0
    ) -> list[QuizSession]:
        query = (
            select(QuizSession)
            .where(QuizSession.teacher_id == teacher_id, QuizSession.school_id == school_id)
            .order_by(QuizSession.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        if status:
            query = query.where(QuizSession.status == status)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    # ── QuizParticipant ──

    async def add_participant(self, quiz_session_id: int, student_id: int, school_id: int) -> QuizParticipant:
        participant = QuizParticipant(
            quiz_session_id=quiz_session_id,
            student_id=student_id,
            school_id=school_id,
        )
        self.db.add(participant)
        await self.db.flush()
        return participant

    async def get_participant(self, quiz_session_id: int, student_id: int) -> Optional[QuizParticipant]:
        result = await self.db.execute(
            select(QuizParticipant).where(
                QuizParticipant.quiz_session_id == quiz_session_id,
                QuizParticipant.student_id == student_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_participants_with_names(self, quiz_session_id: int) -> list[dict]:
        result = await self.db.execute(
            select(
                QuizParticipant,
                User.first_name,
                User.last_name,
            )
            .join(Student, QuizParticipant.student_id == Student.id)
            .join(User, Student.user_id == User.id)
            .where(QuizParticipant.quiz_session_id == quiz_session_id)
            .order_by(QuizParticipant.total_score.desc())
        )
        rows = result.all()
        return [
            {
                "participant": row[0],
                "student_name": f"{row[1]} {row[2]}".strip(),
            }
            for row in rows
        ]

    async def get_participant_count(self, quiz_session_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(QuizParticipant).where(
                QuizParticipant.quiz_session_id == quiz_session_id
            )
        )
        return result.scalar_one()

    async def update_participant_score(self, participant_id: int, score_delta: int, is_correct: bool) -> None:
        values = {
            "total_score": QuizParticipant.total_score + score_delta,
        }
        if is_correct:
            values["correct_answers"] = QuizParticipant.correct_answers + 1
        await self.db.execute(
            update(QuizParticipant).where(QuizParticipant.id == participant_id).values(**values)
        )

    async def set_participant_rank_and_xp(self, participant_id: int, rank: int, xp_earned: int) -> None:
        await self.db.execute(
            update(QuizParticipant).where(QuizParticipant.id == participant_id).values(
                rank=rank, xp_earned=xp_earned, finished_at=func.now()
            )
        )

    # ── QuizAnswer ──

    async def add_answer(
        self,
        quiz_session_id: int,
        participant_id: int,
        school_id: int,
        question_index: int,
        selected_option: int,
        is_correct: bool,
        answer_time_ms: int,
        score: int,
    ) -> QuizAnswer:
        answer = QuizAnswer(
            quiz_session_id=quiz_session_id,
            participant_id=participant_id,
            school_id=school_id,
            question_index=question_index,
            selected_option=selected_option,
            is_correct=is_correct,
            answer_time_ms=answer_time_ms,
            score=score,
        )
        self.db.add(answer)
        await self.db.flush()
        return answer

    async def get_answer(self, participant_id: int, question_index: int) -> Optional[QuizAnswer]:
        result = await self.db.execute(
            select(QuizAnswer).where(
                QuizAnswer.participant_id == participant_id,
                QuizAnswer.question_index == question_index,
            )
        )
        return result.scalar_one_or_none()

    async def count_answers_for_question(self, quiz_session_id: int, question_index: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(QuizAnswer).where(
                QuizAnswer.quiz_session_id == quiz_session_id,
                QuizAnswer.question_index == question_index,
            )
        )
        return result.scalar_one()

    async def get_answer_stats(self, quiz_session_id: int, question_index: int) -> dict:
        """Get answer distribution for a question."""
        result = await self.db.execute(
            select(
                QuizAnswer.selected_option,
                func.count().label("cnt"),
            )
            .where(
                QuizAnswer.quiz_session_id == quiz_session_id,
                QuizAnswer.question_index == question_index,
            )
            .group_by(QuizAnswer.selected_option)
        )
        stats = {}
        for row in result.all():
            stats[str(row[0])] = row[1]
        return stats

    async def get_leaderboard(self, quiz_session_id: int) -> list[dict]:
        return await self.get_participants_with_names(quiz_session_id)
