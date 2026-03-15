"""
Unit tests for Quiz Team Service (Phase 2.2).
Tests: team creation, round-robin assignment, scoring, leaderboard.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.quiz_team_service import QuizTeamService, TEAM_PRESETS
from app.models.quiz import QuizTeam, QuizParticipant


def _make_team(id=1, name="Red", color="#E53E3E", total_score=0, correct_answers=0):
    t = MagicMock(spec=QuizTeam)
    t.id = id
    t.name = name
    t.color = color
    t.total_score = total_score
    t.correct_answers = correct_answers
    return t


class TestCreateTeams:
    """Tests for QuizTeamService.create_teams."""

    @pytest.mark.asyncio
    async def test_create_2_teams(self):
        """Create 2 teams → Red and Blue with correct colors."""
        db = AsyncMock()
        service = QuizTeamService(db)
        service.repo = AsyncMock()

        created = []
        async def mock_create(session_id, school_id, name, color):
            team = _make_team(id=len(created) + 1, name=name, color=color)
            created.append(team)
            return team

        service.repo.create_team = mock_create

        result = await service.create_teams(session_id=1, school_id=100, team_count=2)
        assert len(result) == 2
        assert result[0].name == "Red"
        assert result[0].color == "#E53E3E"
        assert result[1].name == "Blue"
        assert result[1].color == "#3182CE"

    @pytest.mark.asyncio
    async def test_create_6_teams(self):
        """Create max 6 teams → all presets used."""
        db = AsyncMock()
        service = QuizTeamService(db)
        service.repo = AsyncMock()

        created = []
        async def mock_create(session_id, school_id, name, color):
            team = _make_team(id=len(created) + 1, name=name, color=color)
            created.append(team)
            return team

        service.repo.create_team = mock_create

        result = await service.create_teams(session_id=1, school_id=100, team_count=6)
        assert len(result) == 6
        for i, (expected_name, expected_color) in enumerate(TEAM_PRESETS):
            assert result[i].name == expected_name
            assert result[i].color == expected_color

    @pytest.mark.asyncio
    async def test_create_1_team_raises(self):
        """Team count < 2 → ValueError."""
        db = AsyncMock()
        service = QuizTeamService(db)

        with pytest.raises(ValueError, match="between 2 and 6"):
            await service.create_teams(session_id=1, school_id=100, team_count=1)

    @pytest.mark.asyncio
    async def test_create_7_teams_raises(self):
        """Team count > 6 → ValueError."""
        db = AsyncMock()
        service = QuizTeamService(db)

        with pytest.raises(ValueError, match="between 2 and 6"):
            await service.create_teams(session_id=1, school_id=100, team_count=7)

    @pytest.mark.asyncio
    async def test_create_with_custom_names(self):
        """Custom names override presets."""
        db = AsyncMock()
        service = QuizTeamService(db)
        service.repo = AsyncMock()

        created = []
        async def mock_create(session_id, school_id, name, color):
            team = _make_team(id=len(created) + 1, name=name, color=color)
            created.append(team)
            return team

        service.repo.create_team = mock_create

        result = await service.create_teams(
            session_id=1, school_id=100, team_count=2,
            custom_names=["Alpha", "Beta"],
        )
        assert result[0].name == "Alpha"
        assert result[1].name == "Beta"
        # Colors still from presets
        assert result[0].color == "#E53E3E"
        assert result[1].color == "#3182CE"


class TestAssignToTeam:
    """Tests for QuizTeamService.assign_to_team (round-robin)."""

    @pytest.mark.asyncio
    async def test_assign_to_smallest_team(self):
        """Participant assigned to team with fewest members."""
        db = AsyncMock()
        service = QuizTeamService(db)
        team = _make_team(id=2, name="Blue")

        service.repo = AsyncMock()
        service.repo.find_smallest_team = AsyncMock(return_value=team)
        service.repo.assign_participant_to_team = AsyncMock()

        result = await service.assign_to_team(session_id=1, participant_id=10)
        assert result.id == 2
        assert result.name == "Blue"
        service.repo.assign_participant_to_team.assert_called_once_with(10, 2)

    @pytest.mark.asyncio
    async def test_assign_no_teams_returns_none(self):
        """No teams → returns None."""
        db = AsyncMock()
        service = QuizTeamService(db)
        service.repo = AsyncMock()
        service.repo.find_smallest_team = AsyncMock(return_value=None)

        result = await service.assign_to_team(session_id=1, participant_id=10)
        assert result is None


class TestUpdateTeamScore:
    """Tests for QuizTeamService.update_team_score."""

    @pytest.mark.asyncio
    async def test_update_score_delegates_to_repo(self):
        """update_team_score delegates to repo correctly."""
        db = AsyncMock()
        service = QuizTeamService(db)
        service.repo = AsyncMock()

        await service.update_team_score(team_id=1, score_delta=500, is_correct=True)
        service.repo.update_team_score.assert_called_once_with(1, 500, True)


class TestTeamLeaderboard:
    """Tests for QuizTeamService.get_team_leaderboard."""

    @pytest.mark.asyncio
    async def test_leaderboard_returns_sorted_teams(self):
        """Leaderboard returns teams sorted by score."""
        db = AsyncMock()
        service = QuizTeamService(db)

        team1 = _make_team(id=1, name="Red", total_score=3000, correct_answers=3)
        team2 = _make_team(id=2, name="Blue", total_score=5000, correct_answers=5)

        service.repo = AsyncMock()
        service.repo.get_teams_with_member_counts = AsyncMock(return_value=[
            {"team": team2, "member_count": 3},
            {"team": team1, "member_count": 2},
        ])

        result = await service.get_team_leaderboard(session_id=1)
        assert len(result) == 2
        # First should be Blue (higher score)
        assert result[0].name == "Blue"
        assert result[0].total_score == 5000
        assert result[0].member_count == 3
        assert result[1].name == "Red"
        assert result[1].total_score == 3000


class TestTeamProgress:
    """Tests for QuizTeamService.get_team_progress (Space Race)."""

    @pytest.mark.asyncio
    async def test_progress_returns_correct_answers(self):
        """Space Race uses correct_answers for visualization."""
        db = AsyncMock()
        service = QuizTeamService(db)

        team1 = _make_team(id=1, name="Red", total_score=2000, correct_answers=2)
        team2 = _make_team(id=2, name="Blue", total_score=3000, correct_answers=4)

        service.repo = AsyncMock()
        service.repo.get_teams_with_member_counts = AsyncMock(return_value=[
            {"team": team2, "member_count": 2},
            {"team": team1, "member_count": 2},
        ])

        result = await service.get_team_progress(session_id=1)
        assert len(result) == 2
        assert result[0]["correct_answers"] == 4
        assert result[0]["name"] == "Blue"
        assert result[1]["correct_answers"] == 2
