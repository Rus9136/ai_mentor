"""
Unit tests for Quiz Service: Phase 2.2 mode-specific logic.
Tests: team mode creation, quick_question mode, self_paced mode, accuracy scoring.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from app.services.quiz_service import QuizService
from app.services.quiz_scoring import MAX_QUESTION_SCORE
from app.models.quiz import QuizSession, QuizParticipant, QuizSessionStatus
from app.schemas.quiz import QuizSessionSettings


def _make_session(
    id=1, teacher_id=10, school_id=100,
    status=QuizSessionStatus.LOBBY, question_count=5,
    settings=None, test_id=1, mode="classic",
):
    session = MagicMock(spec=QuizSession)
    session.id = id
    session.teacher_id = teacher_id
    session.school_id = school_id
    session.status = status
    session.question_count = question_count
    session.settings = settings or {"time_per_question_ms": 30000, "mode": mode}
    session.test_id = test_id
    session.join_code = "123456"
    session.started_at = None
    session.finished_at = None
    session.current_question_index = -1
    type(session).mode = PropertyMock(return_value=mode)
    return session


def _make_participant(id=1, student_id=20, school_id=100, team_id=None):
    p = MagicMock(spec=QuizParticipant)
    p.id = id
    p.student_id = student_id
    p.school_id = school_id
    p.team_id = team_id
    p.total_score = 0
    p.correct_answers = 0
    p.current_streak = 0
    p.max_streak = 0
    return p


# ========== Accuracy Mode Scoring ==========


class TestAccuracyModeScoring:
    """Tests for scoring_mode='accuracy' (used in self-paced and optional in classic)."""

    def test_accuracy_correct_returns_max(self):
        """Accuracy mode: correct answer = 1000 regardless of time."""
        score = QuizService._calculate_score(
            is_correct=True, answer_time_ms=15000, time_limit_ms=30000,
            scoring_mode="accuracy",
        )
        assert score == MAX_QUESTION_SCORE

    def test_accuracy_correct_instant_also_max(self):
        """Accuracy mode: instant correct = 1000 (no speed bonus)."""
        score = QuizService._calculate_score(
            is_correct=True, answer_time_ms=0, time_limit_ms=30000,
            scoring_mode="accuracy",
        )
        assert score == MAX_QUESTION_SCORE

    def test_accuracy_incorrect_returns_zero(self):
        """Accuracy mode: incorrect = 0."""
        score = QuizService._calculate_score(
            is_correct=False, answer_time_ms=5000, time_limit_ms=30000,
            scoring_mode="accuracy",
        )
        assert score == 0

    def test_speed_correct_varies_with_time(self):
        """Speed mode: score depends on answer_time_ms."""
        fast = QuizService._calculate_score(
            is_correct=True, answer_time_ms=1000, time_limit_ms=30000,
            scoring_mode="speed",
        )
        slow = QuizService._calculate_score(
            is_correct=True, answer_time_ms=25000, time_limit_ms=30000,
            scoring_mode="speed",
        )
        assert fast > slow  # Faster = more points


# ========== Quick Question Mode ==========


class TestQuickQuestionMode:
    """Tests for quick_question mode session creation."""

    @pytest.mark.asyncio
    async def test_create_quick_question_no_test_id(self):
        """Quick question mode creates session without test_id."""
        db = AsyncMock()
        service = QuizService(db)

        created_session = _make_session(mode="quick_question", test_id=None, question_count=0)
        service.repo = AsyncMock()
        service.repo.check_join_code_exists = AsyncMock(return_value=False)
        service.repo.create_session = AsyncMock(return_value=created_session)

        settings = QuizSessionSettings(mode="quick_question")
        result = await service.create_session(
            teacher_id=10, school_id=100, test_id=None, settings=settings,
        )
        assert result.test_id is None
        assert result.question_count == 0

        # Verify create_session was called with test_id=None
        call_kwargs = service.repo.create_session.call_args.kwargs
        assert call_kwargs["test_id"] is None
        assert call_kwargs["question_count"] == 0

    @pytest.mark.asyncio
    async def test_quick_question_requires_no_test(self):
        """Quick question mode should not require test_id."""
        db = AsyncMock()
        service = QuizService(db)

        created_session = _make_session(mode="quick_question", test_id=None, question_count=0)
        service.repo = AsyncMock()
        service.repo.check_join_code_exists = AsyncMock(return_value=False)
        service.repo.create_session = AsyncMock(return_value=created_session)

        settings = QuizSessionSettings(mode="quick_question")
        # Should not raise even without test_id
        result = await service.create_session(
            teacher_id=10, school_id=100, test_id=None, settings=settings,
        )
        assert result is not None


# ========== Team Mode Join ==========


class TestTeamModeJoin:
    """Tests for join_session with team mode."""

    @pytest.mark.asyncio
    async def test_join_team_mode_assigns_team(self):
        """Joining team mode session → auto-assigned to team."""
        db = AsyncMock()
        service = QuizService(db)

        session = _make_session(mode="team", status=QuizSessionStatus.LOBBY, school_id=100)
        participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=None)  # New participant
        service.repo.add_participant = AsyncMock(return_value=participant)
        service.repo.get_participant_count = AsyncMock(return_value=1)

        # Mock team service (imported locally inside join_session)
        team_mock = MagicMock()
        team_mock.id = 1
        team_mock.name = "Red"
        team_mock.color = "#E53E3E"

        mock_team_service_instance = AsyncMock()
        mock_team_service_instance.assign_to_team = AsyncMock(return_value=team_mock)

        with patch.dict("sys.modules", {}):
            with patch("app.services.quiz_team_service.QuizTeamService", return_value=mock_team_service_instance):
                result = await service.join_session(
                    join_code="123456", student_id=20, school_id=100,
                )

        assert result["team_id"] == 1
        assert result["team_name"] == "Red"
        assert result["team_color"] == "#E53E3E"
        assert result["mode"] == "team"

    @pytest.mark.asyncio
    async def test_join_classic_mode_no_team(self):
        """Joining classic mode → no team info."""
        db = AsyncMock()
        service = QuizService(db)

        session = _make_session(mode="classic", status=QuizSessionStatus.LOBBY, school_id=100)
        participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=None)
        service.repo.add_participant = AsyncMock(return_value=participant)
        service.repo.get_participant_count = AsyncMock(return_value=1)

        result = await service.join_session(
            join_code="123456", student_id=20, school_id=100,
        )
        assert "team_id" not in result
        assert result["mode"] == "classic"

    @pytest.mark.asyncio
    async def test_join_team_mode_idempotent_returns_existing_team(self):
        """Re-joining team mode → returns existing team assignment."""
        db = AsyncMock()
        service = QuizService(db)

        session = _make_session(mode="team", status=QuizSessionStatus.LOBBY, school_id=100)
        existing_participant = _make_participant(team_id=2)

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=existing_participant)
        service.repo.get_participant_count = AsyncMock(return_value=3)

        # Mock team repo lookup (imported locally inside join_session)
        team_mock = MagicMock()
        team_mock.id = 2
        team_mock.name = "Blue"
        team_mock.color = "#3182CE"

        mock_repo_instance = AsyncMock()
        mock_repo_instance.get_team_by_id = AsyncMock(return_value=team_mock)

        with patch("app.repositories.quiz_team_repo.QuizTeamRepository", return_value=mock_repo_instance):
            result = await service.join_session(
                join_code="123456", student_id=20, school_id=100,
            )

        assert result["team_id"] == 2
        assert result["team_name"] == "Blue"
        # add_participant should NOT be called (already joined)
        service.repo.add_participant.assert_not_called()


# ========== Self-Paced Mode Creation ==========


class TestSelfPacedModeCreation:
    """Tests for self-paced mode: forces accuracy scoring."""

    @pytest.mark.asyncio
    async def test_self_paced_forces_accuracy_scoring(self):
        """Self-paced mode forces scoring_mode to 'accuracy'."""
        db = AsyncMock()
        service = QuizService(db)

        # Mock test loading
        mock_test = MagicMock()
        mock_question = MagicMock()
        mock_question.question_type = MagicMock()
        mock_question.question_type.__eq__ = lambda self, other: True  # any QuestionType match
        mock_question.is_deleted = False
        mock_test.questions = [mock_question]

        from app.models.test import QuestionType
        mock_question.question_type = QuestionType.SINGLE_CHOICE

        created_session = _make_session(mode="self_paced")

        service.repo = AsyncMock()
        service.repo.check_join_code_exists = AsyncMock(return_value=False)
        service.repo.create_session = AsyncMock(return_value=created_session)

        with patch.object(service, "db") as mock_db:
            mock_result = AsyncMock()
            mock_result.scalar_one_or_none = MagicMock(return_value=mock_test)
            mock_db.execute = AsyncMock(return_value=mock_result)

            settings = QuizSessionSettings(mode="self_paced", scoring_mode="speed")
            result = await service.create_session(
                teacher_id=10, school_id=100, test_id=1, settings=settings,
            )

        # Verify settings passed to create_session has scoring_mode = accuracy
        call_kwargs = service.repo.create_session.call_args.kwargs
        assert call_kwargs["settings"]["scoring_mode"] == "accuracy"


# ========== Streak Bonus (Phase 2.1 — verify still works with modes) ==========


class TestStreakBonus:
    """Verify streak bonus calculation works correctly."""

    def test_no_streak_bonus_below_2(self):
        assert QuizService._calculate_streak_bonus(0) == 0
        assert QuizService._calculate_streak_bonus(1) == 0

    def test_streak_2_bonus_100(self):
        assert QuizService._calculate_streak_bonus(2) == 100

    def test_streak_3_bonus_200(self):
        assert QuizService._calculate_streak_bonus(3) == 200

    def test_streak_4_bonus_300(self):
        assert QuizService._calculate_streak_bonus(4) == 300

    def test_streak_5_plus_capped_at_500(self):
        assert QuizService._calculate_streak_bonus(5) == 500
        assert QuizService._calculate_streak_bonus(10) == 500
