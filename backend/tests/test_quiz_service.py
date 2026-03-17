"""
Unit tests for Quiz Battle Service: scoring, XP, state machine.
"""
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.quiz_service import QuizService
from app.services.quiz_scoring import MAX_QUESTION_SCORE
from app.models.quiz import QuizSession, QuizParticipant, QuizAnswer, QuizSessionStatus


# ========== Scoring Tests ==========


class TestCalculateScore:
    """Unit tests for _calculate_score static method."""

    def test_correct_mid_time(self):
        """5000ms out of 30000ms → 917."""
        score = QuizService._calculate_score(is_correct=True, answer_time_ms=5000, time_limit_ms=30000)
        assert score == 917

    def test_correct_instant(self):
        """0ms → max score 1000."""
        score = QuizService._calculate_score(is_correct=True, answer_time_ms=0, time_limit_ms=30000)
        assert score == 1000

    def test_correct_at_time_limit(self):
        """30000ms out of 30000ms → 500."""
        score = QuizService._calculate_score(is_correct=True, answer_time_ms=30000, time_limit_ms=30000)
        assert score == 500

    def test_incorrect_returns_zero(self):
        """Incorrect answer always returns 0 regardless of time."""
        assert QuizService._calculate_score(is_correct=False, answer_time_ms=0, time_limit_ms=30000) == 0
        assert QuizService._calculate_score(is_correct=False, answer_time_ms=5000, time_limit_ms=30000) == 0
        assert QuizService._calculate_score(is_correct=False, answer_time_ms=30000, time_limit_ms=30000) == 0

    def test_correct_over_time_limit(self):
        """Answer time > time_limit → clamp at 0 via max(0, ...)."""
        score = QuizService._calculate_score(is_correct=True, answer_time_ms=60000, time_limit_ms=30000)
        assert score == 0

    def test_score_always_integer(self):
        """Score is always rounded to int."""
        score = QuizService._calculate_score(is_correct=True, answer_time_ms=7777, time_limit_ms=30000)
        assert isinstance(score, int)

    def test_different_time_limits(self):
        """Score scales with different time limits."""
        # 10s out of 60s → time_factor = 1 - (10000/60000)/2 = 1 - 0.0833 = 0.9167
        score = QuizService._calculate_score(is_correct=True, answer_time_ms=10000, time_limit_ms=60000)
        assert score == 917


# ========== XP Tests ==========


class TestCalculateXp:
    """Unit tests for _calculate_xp static method."""

    def test_rank1_perfect(self):
        """Rank 1, 10/10 correct → 10 + 50 + 50 + 25 = 135."""
        xp = QuizService._calculate_xp(rank=1, correct_answers=10, total_questions=10)
        assert xp == 135

    def test_rank2_partial(self):
        """Rank 2, 7/10 correct → 10 + 35 + 30 = 75."""
        xp = QuizService._calculate_xp(rank=2, correct_answers=7, total_questions=10)
        assert xp == 75

    def test_rank4_zero_correct(self):
        """Rank 4+, 0 correct → only participation XP = 10."""
        xp = QuizService._calculate_xp(rank=4, correct_answers=0, total_questions=10)
        assert xp == 10

    def test_rank1_not_perfect(self):
        """Rank 1, 5/10 → 10 + 25 + 50 = 85 (no perfect bonus)."""
        xp = QuizService._calculate_xp(rank=1, correct_answers=5, total_questions=10)
        assert xp == 85

    def test_rank3(self):
        """Rank 3, 8/10 → 10 + 40 + 15 = 65."""
        xp = QuizService._calculate_xp(rank=3, correct_answers=8, total_questions=10)
        assert xp == 65

    def test_rank2_perfect(self):
        """Rank 2, 10/10 → 10 + 50 + 30 + 25 = 115."""
        xp = QuizService._calculate_xp(rank=2, correct_answers=10, total_questions=10)
        assert xp == 115

    def test_zero_total_no_perfect_bonus(self):
        """total_questions=0, correct=0 → no perfect bonus even if equal."""
        xp = QuizService._calculate_xp(rank=1, correct_answers=0, total_questions=0)
        assert xp == 60  # 10 + 0 + 50, no perfect (total=0 guard)


# ========== State Machine Tests (with mocked DB) ==========


def _make_session(
    id=1,
    teacher_id=10,
    school_id=100,
    status=QuizSessionStatus.LOBBY,
    question_count=5,
    current_question_index=-1,
    settings=None,
    test_id=1,
):
    """Create a mock QuizSession object."""
    session = MagicMock(spec=QuizSession)
    session.id = id
    session.teacher_id = teacher_id
    session.school_id = school_id
    session.status = status
    session.question_count = question_count
    session.current_question_index = current_question_index
    session.settings = settings or {"time_per_question_ms": 30000}
    session.test_id = test_id
    session.started_at = None
    session.finished_at = None
    session.join_code = "123456"
    return session


def _make_participant(id=1, student_id=20, school_id=100, total_score=0, correct_answers=0):
    """Create a mock QuizParticipant object."""
    p = MagicMock(spec=QuizParticipant)
    p.id = id
    p.student_id = student_id
    p.school_id = school_id
    p.total_score = total_score
    p.correct_answers = correct_answers
    return p


def _make_answer(is_correct=True, score=500):
    """Create a mock QuizAnswer object."""
    a = MagicMock(spec=QuizAnswer)
    a.is_correct = is_correct
    a.score = score
    return a


class TestStartSession:
    """Tests for QuizService.start_session state transitions."""

    @pytest.mark.asyncio
    async def test_start_from_lobby_ok(self):
        """Start session when status=lobby → OK."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant_count = AsyncMock(return_value=3)
        service.repo.update_session = AsyncMock()

        result = await service.start_session(session_id=1, teacher_id=10)
        assert result.status == QuizSessionStatus.IN_PROGRESS
        service.repo.update_session.assert_called_once()

    @pytest.mark.asyncio
    async def test_start_from_finished_raises(self):
        """Start session when status=finished → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.FINISHED)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="not in lobby"):
            await service.start_session(session_id=1, teacher_id=10)

    @pytest.mark.asyncio
    async def test_start_wrong_teacher_raises(self):
        """Start session with wrong teacher_id → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(teacher_id=10)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="Not the session owner"):
            await service.start_session(session_id=1, teacher_id=999)

    @pytest.mark.asyncio
    async def test_start_no_participants_raises(self):
        """Start session with 0 participants → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant_count = AsyncMock(return_value=0)

        with pytest.raises(ValueError, match="No participants"):
            await service.start_session(session_id=1, teacher_id=10)

    @pytest.mark.asyncio
    async def test_start_not_found_raises(self):
        """Start session with invalid id → ValueError."""
        db = AsyncMock()
        service = QuizService(db)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="not found"):
            await service.start_session(session_id=999, teacher_id=10)


class TestCancelSession:
    """Tests for QuizService.cancel_session state transitions."""

    @pytest.mark.asyncio
    async def test_cancel_from_lobby_ok(self):
        """Cancel session from lobby → OK."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.update_session = AsyncMock()

        result = await service.cancel_session(session_id=1, teacher_id=10)
        assert result.status == QuizSessionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_from_in_progress_ok(self):
        """Cancel session from in_progress → OK."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.IN_PROGRESS)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.update_session = AsyncMock()

        result = await service.cancel_session(session_id=1, teacher_id=10)
        assert result.status == QuizSessionStatus.CANCELLED

    @pytest.mark.asyncio
    async def test_cancel_from_finished_raises(self):
        """Cancel session when status=finished → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.FINISHED)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="already ended"):
            await service.cancel_session(session_id=1, teacher_id=10)

    @pytest.mark.asyncio
    async def test_cancel_from_cancelled_raises(self):
        """Cancel already cancelled session → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.CANCELLED)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="already ended"):
            await service.cancel_session(session_id=1, teacher_id=10)

    @pytest.mark.asyncio
    async def test_cancel_wrong_teacher_raises(self):
        """Cancel session with wrong teacher → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(teacher_id=10)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="Not the session owner"):
            await service.cancel_session(session_id=1, teacher_id=999)


class TestSubmitAnswer:
    """Tests for QuizService.submit_answer."""

    @pytest.mark.asyncio
    async def test_idempotent_already_answered(self):
        """Re-submitting same answer returns already_answered=True."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.IN_PROGRESS, current_question_index=0)
        participant = _make_participant(total_score=500)
        existing_answer = _make_answer(is_correct=True, score=500)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service.repo.get_answer = AsyncMock(return_value=existing_answer)

        result = await service.submit_answer(
            session_id=1, student_id=20, question_index=0, selected_option=1, answer_time_ms=5000
        )
        assert result["already_answered"] is True
        assert result["is_correct"] is True
        assert result["score"] == 500

    @pytest.mark.asyncio
    async def test_wrong_question_index_raises(self):
        """Submit answer for wrong question_index → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.IN_PROGRESS, current_question_index=2)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="Wrong question index"):
            await service.submit_answer(
                session_id=1, student_id=20, question_index=5, selected_option=0, answer_time_ms=1000
            )

    @pytest.mark.asyncio
    async def test_session_not_in_progress_raises(self):
        """Submit answer when session not in progress → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY, current_question_index=0)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="not in progress"):
            await service.submit_answer(
                session_id=1, student_id=20, question_index=0, selected_option=0, answer_time_ms=1000
            )

    @pytest.mark.asyncio
    async def test_not_participant_raises(self):
        """Submit answer when student is not a participant → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.IN_PROGRESS, current_question_index=0)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Not a participant"):
            await service.submit_answer(
                session_id=1, student_id=20, question_index=0, selected_option=0, answer_time_ms=1000
            )


class TestJoinSession:
    """Tests for QuizService.join_session."""

    @pytest.mark.asyncio
    async def test_join_in_progress_raises(self):
        """Join session when status=in_progress → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.IN_PROGRESS)

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="not accepting participants"):
            await service.join_session(join_code="123456", student_id=20, school_id=100)

    @pytest.mark.asyncio
    async def test_join_wrong_school_raises(self):
        """Join session from different school → ValueError."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(school_id=100)

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="different school"):
            await service.join_session(join_code="123456", student_id=20, school_id=999)

    @pytest.mark.asyncio
    async def test_join_invalid_code_raises(self):
        """Join with invalid code → ValueError."""
        db = AsyncMock()
        service = QuizService(db)

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Invalid quiz code"):
            await service.join_session(join_code="000000", student_id=20, school_id=100)

    @pytest.mark.asyncio
    async def test_join_lobby_ok(self):
        """Join session in lobby → OK, returns session info."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY, school_id=100)

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=None)
        service.repo.add_participant = AsyncMock()
        service.repo.get_participant_count = AsyncMock(return_value=1)

        result = await service.join_session(join_code="123456", student_id=20, school_id=100)
        assert result["quiz_session_id"] == 1
        assert result["status"] == "lobby"
        assert result["participant_count"] == 1

    @pytest.mark.asyncio
    async def test_join_idempotent(self):
        """Join session twice → idempotent, no duplicate participant."""
        db = AsyncMock()
        service = QuizService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY, school_id=100)
        existing_participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session_by_join_code = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=existing_participant)
        service.repo.get_participant_count = AsyncMock(return_value=1)

        result = await service.join_session(join_code="123456", student_id=20, school_id=100)
        # add_participant should NOT be called (already joined)
        service.repo.add_participant.assert_not_called()
        assert result["participant_count"] == 1
