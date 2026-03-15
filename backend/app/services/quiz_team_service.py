"""
Quiz Team Service: team creation, assignment, scoring, leaderboard.
"""
import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizTeam
from app.repositories.quiz_team_repo import QuizTeamRepository
from app.schemas.quiz import QuizTeamResponse

logger = logging.getLogger(__name__)

# Predefined team names and colors
TEAM_PRESETS = [
    ("Red", "#E53E3E"),
    ("Blue", "#3182CE"),
    ("Green", "#38A169"),
    ("Yellow", "#D69E2E"),
    ("Purple", "#805AD5"),
    ("Orange", "#DD6B20"),
]


class QuizTeamService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = QuizTeamRepository(db)

    async def create_teams(
        self,
        session_id: int,
        school_id: int,
        team_count: int,
        custom_names: Optional[list[str]] = None,
    ) -> list[QuizTeam]:
        """Create teams for a quiz session."""
        if team_count < 2 or team_count > 6:
            raise ValueError("Team count must be between 2 and 6")

        teams = []
        for i in range(team_count):
            name = custom_names[i] if custom_names and i < len(custom_names) else TEAM_PRESETS[i][0]
            color = TEAM_PRESETS[i][1]
            team = await self.repo.create_team(session_id, school_id, name, color)
            teams.append(team)

        return teams

    async def assign_to_team(self, session_id: int, participant_id: int) -> Optional[QuizTeam]:
        """Auto-assign participant to team with fewest members (round-robin)."""
        team = await self.repo.find_smallest_team(session_id)
        if not team:
            return None
        await self.repo.assign_participant_to_team(participant_id, team.id)
        return team

    async def update_team_score(self, team_id: int, score_delta: int, is_correct: bool) -> None:
        """Update team aggregate score after a member answers."""
        await self.repo.update_team_score(team_id, score_delta, is_correct)

    async def get_team_leaderboard(self, session_id: int) -> list[QuizTeamResponse]:
        """Get teams sorted by total_score DESC with member counts."""
        data = await self.repo.get_teams_with_member_counts(session_id)
        return [
            QuizTeamResponse(
                id=d["team"].id,
                name=d["team"].name,
                color=d["team"].color,
                total_score=d["team"].total_score,
                correct_answers=d["team"].correct_answers,
                member_count=d["member_count"],
            )
            for d in data
        ]

    async def get_team_progress(self, session_id: int) -> list[dict]:
        """Get team progress for Space Race (correct_answers per team)."""
        data = await self.repo.get_teams_with_member_counts(session_id)
        return [
            {
                "id": d["team"].id,
                "name": d["team"].name,
                "color": d["team"].color,
                "correct_answers": d["team"].correct_answers,
                "total_score": d["team"].total_score,
            }
            for d in data
        ]

    async def get_teams(self, session_id: int) -> list[QuizTeam]:
        """Get all teams for a session."""
        return await self.repo.get_teams(session_id)
