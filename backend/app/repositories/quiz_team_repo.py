"""
Repository for Quiz Team CRUD operations.
"""
import logging
from typing import Optional
from sqlalchemy import select, func, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizTeam, QuizParticipant

logger = logging.getLogger(__name__)


class QuizTeamRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_team(
        self, quiz_session_id: int, school_id: int, name: str, color: str,
    ) -> QuizTeam:
        team = QuizTeam(
            quiz_session_id=quiz_session_id,
            school_id=school_id,
            name=name,
            color=color,
        )
        self.db.add(team)
        await self.db.flush()
        return team

    async def get_teams(self, quiz_session_id: int) -> list[QuizTeam]:
        result = await self.db.execute(
            select(QuizTeam)
            .where(QuizTeam.quiz_session_id == quiz_session_id)
            .order_by(QuizTeam.id)
        )
        return list(result.scalars().all())

    async def get_team_by_id(self, team_id: int) -> Optional[QuizTeam]:
        result = await self.db.execute(
            select(QuizTeam).where(QuizTeam.id == team_id)
        )
        return result.scalar_one_or_none()

    async def get_team_member_count(self, team_id: int) -> int:
        result = await self.db.execute(
            select(func.count()).select_from(QuizParticipant)
            .where(QuizParticipant.team_id == team_id)
        )
        return result.scalar_one()

    async def get_teams_with_member_counts(self, quiz_session_id: int) -> list[dict]:
        """Get teams with member counts, sorted by total_score DESC."""
        result = await self.db.execute(
            select(
                QuizTeam,
                func.count(QuizParticipant.id).label("member_count"),
            )
            .outerjoin(QuizParticipant, QuizParticipant.team_id == QuizTeam.id)
            .where(QuizTeam.quiz_session_id == quiz_session_id)
            .group_by(QuizTeam.id)
            .order_by(QuizTeam.total_score.desc())
        )
        return [
            {"team": row[0], "member_count": row[1]}
            for row in result.all()
        ]

    async def update_team_score(
        self, team_id: int, score_delta: int, is_correct: bool,
    ) -> None:
        values = {"total_score": QuizTeam.total_score + score_delta}
        if is_correct:
            values["correct_answers"] = QuizTeam.correct_answers + 1
        await self.db.execute(
            update(QuizTeam).where(QuizTeam.id == team_id).values(**values)
        )

    async def find_smallest_team(self, quiz_session_id: int) -> Optional[QuizTeam]:
        """Find team with fewest members (for round-robin assignment)."""
        result = await self.db.execute(
            select(
                QuizTeam,
                func.count(QuizParticipant.id).label("cnt"),
            )
            .outerjoin(QuizParticipant, QuizParticipant.team_id == QuizTeam.id)
            .where(QuizTeam.quiz_session_id == quiz_session_id)
            .group_by(QuizTeam.id)
            .order_by(func.count(QuizParticipant.id).asc(), QuizTeam.id.asc())
            .limit(1)
        )
        row = result.first()
        return row[0] if row else None

    async def assign_participant_to_team(self, participant_id: int, team_id: int) -> None:
        await self.db.execute(
            update(QuizParticipant)
            .where(QuizParticipant.id == participant_id)
            .values(team_id=team_id)
        )
