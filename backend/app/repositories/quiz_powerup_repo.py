"""
Repository for quiz power-ups CRUD.
"""
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizParticipantPowerup


class QuizPowerupRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_powerup(
        self,
        quiz_session_id: int,
        participant_id: int,
        school_id: int,
        powerup_type: str,
        question_index: int,
        xp_cost: int,
    ) -> QuizParticipantPowerup:
        powerup = QuizParticipantPowerup(
            quiz_session_id=quiz_session_id,
            participant_id=participant_id,
            school_id=school_id,
            powerup_type=powerup_type,
            question_index=question_index,
            xp_cost=xp_cost,
        )
        self.db.add(powerup)
        await self.db.flush()
        return powerup

    async def get_powerup(
        self, participant_id: int, question_index: int,
    ) -> Optional[QuizParticipantPowerup]:
        result = await self.db.execute(
            select(QuizParticipantPowerup).where(
                QuizParticipantPowerup.participant_id == participant_id,
                QuizParticipantPowerup.question_index == question_index,
            )
        )
        return result.scalar_one_or_none()

    async def mark_applied(self, powerup_id: int) -> None:
        await self.db.execute(
            update(QuizParticipantPowerup)
            .where(QuizParticipantPowerup.id == powerup_id)
            .values(applied=True)
        )
