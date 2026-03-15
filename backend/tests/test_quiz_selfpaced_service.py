"""
Unit tests for Quiz Self-Paced Service (Phase 2.2).
Tests: next question, submit answer, student progress, idempotency.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock

from app.services.quiz_selfpaced_service import QuizSelfPacedService, MAX_QUESTION_SCORE
from app.models.quiz import QuizSession, QuizParticipant, QuizAnswer, QuizSessionStatus
from app.schemas.quiz import QuizQuestionOut


def _make_session(
    id=1, status=QuizSessionStatus.IN_PROGRESS, question_count=5,
    test_id=1, settings=None, mode="self_paced",
):
    session = MagicMock(spec=QuizSession)
    session.id = id
    session.status = status
    session.question_count = question_count
    session.test_id = test_id
    session.school_id = 100
    session.settings = settings or {"scoring_mode": "accuracy", "mode": "self_paced"}
    type(session).mode = PropertyMock(return_value=mode)
    return session


def _make_participant(id=1, student_id=20, total_score=0, correct_answers=0):
    p = MagicMock(spec=QuizParticipant)
    p.id = id
    p.student_id = student_id
    p.total_score = total_score
    p.correct_answers = correct_answers
    return p


def _make_answer(is_correct=True, score=1000):
    a = MagicMock(spec=QuizAnswer)
    a.is_correct = is_correct
    a.score = score
    return a


def _make_question_out(index=0):
    return QuizQuestionOut(
        index=index,
        text="What is 2+2?",
        options=["3", "4", "5", "6"],
        time_limit_ms=30000,
    )


class TestGetNextQuestion:
    """Tests for QuizSelfPacedService.get_next_question."""

    @pytest.mark.asyncio
    async def test_returns_next_unanswered(self):
        """Get next question after 2 answered → returns question index 2."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=5)
        participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)

        question_out = _make_question_out(index=2)
        service._quiz_service = AsyncMock()
        service._quiz_service._load_question = AsyncMock(return_value=question_out)

        # Student has answered 2 questions
        service._count_student_answers = AsyncMock(return_value=2)

        result = await service.get_next_question(session_id=1, student_id=20)
        assert result is not None
        assert result.question.index == 2
        assert result.answered_count == 2
        assert result.total_questions == 5
        assert result.is_last is False

    @pytest.mark.asyncio
    async def test_last_question_flag(self):
        """Last question → is_last = True."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=3)
        participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)

        question_out = _make_question_out(index=2)
        service._quiz_service = AsyncMock()
        service._quiz_service._load_question = AsyncMock(return_value=question_out)
        service._count_student_answers = AsyncMock(return_value=2)

        result = await service.get_next_question(session_id=1, student_id=20)
        assert result.is_last is True

    @pytest.mark.asyncio
    async def test_all_answered_returns_none(self):
        """All questions answered → returns None."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=5)
        participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service._count_student_answers = AsyncMock(return_value=5)

        result = await service.get_next_question(session_id=1, student_id=20)
        assert result is None

    @pytest.mark.asyncio
    async def test_not_in_progress_raises(self):
        """Session not in progress → ValueError."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(status=QuizSessionStatus.LOBBY)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="not in progress"):
            await service.get_next_question(session_id=1, student_id=20)

    @pytest.mark.asyncio
    async def test_not_self_paced_raises(self):
        """Non-self-paced session → ValueError."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(mode="classic")

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)

        with pytest.raises(ValueError, match="not self-paced"):
            await service.get_next_question(session_id=1, student_id=20)

    @pytest.mark.asyncio
    async def test_not_participant_raises(self):
        """Non-participant → ValueError."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session()

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=None)

        with pytest.raises(ValueError, match="Not a participant"):
            await service.get_next_question(session_id=1, student_id=20)


class TestSubmitAnswer:
    """Tests for QuizSelfPacedService.submit_answer."""

    @pytest.mark.asyncio
    async def test_correct_answer_scores_1000(self):
        """Correct answer → 1000 points (accuracy mode)."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=5)
        participant = _make_participant(total_score=0, correct_answers=0)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service.repo.get_answer = AsyncMock(return_value=None)  # Not already answered
        service.repo.add_answer = AsyncMock()
        service.repo.update_participant_score = AsyncMock()

        service._quiz_service = AsyncMock()
        service._quiz_service._check_answer = AsyncMock(return_value=True)
        service._quiz_service._get_correct_option_index = AsyncMock(return_value=1)

        service._count_student_answers = AsyncMock(return_value=1)

        result = await service.submit_answer(
            session_id=1, student_id=20, question_index=0, selected_option=1,
        )
        assert result.is_correct is True
        assert result.score == MAX_QUESTION_SCORE  # 1000
        assert result.correct_option == 1
        assert result.total_score == 1000  # 0 + 1000
        assert result.correct_answers == 1

    @pytest.mark.asyncio
    async def test_incorrect_answer_scores_0(self):
        """Incorrect answer → 0 points."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=5)
        participant = _make_participant(total_score=1000, correct_answers=1)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service.repo.get_answer = AsyncMock(return_value=None)
        service.repo.add_answer = AsyncMock()
        service.repo.update_participant_score = AsyncMock()

        service._quiz_service = AsyncMock()
        service._quiz_service._check_answer = AsyncMock(return_value=False)
        service._quiz_service._get_correct_option_index = AsyncMock(return_value=2)

        service._count_student_answers = AsyncMock(return_value=2)

        result = await service.submit_answer(
            session_id=1, student_id=20, question_index=1, selected_option=0,
        )
        assert result.is_correct is False
        assert result.score == 0
        assert result.correct_option == 2
        assert result.total_score == 1000  # unchanged

    @pytest.mark.asyncio
    async def test_idempotent_already_answered(self):
        """Re-submitting returns cached result."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=5)
        participant = _make_participant(total_score=1000, correct_answers=1)
        existing_answer = _make_answer(is_correct=True, score=1000)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service.repo.get_answer = AsyncMock(return_value=existing_answer)

        service._quiz_service = AsyncMock()
        service._quiz_service._get_correct_option_index = AsyncMock(return_value=1)
        service._count_student_answers = AsyncMock(return_value=1)

        result = await service.submit_answer(
            session_id=1, student_id=20, question_index=0, selected_option=1,
        )
        assert result.is_correct is True
        assert result.score == 1000
        # add_answer should NOT be called
        service.repo.add_answer.assert_not_called()

    @pytest.mark.asyncio
    async def test_last_answer_sets_is_finished(self):
        """Answering last question → is_finished = True."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=3)
        participant = _make_participant(total_score=2000, correct_answers=2)

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service.repo.get_answer = AsyncMock(return_value=None)
        service.repo.add_answer = AsyncMock()
        service.repo.update_participant_score = AsyncMock()

        service._quiz_service = AsyncMock()
        service._quiz_service._check_answer = AsyncMock(return_value=True)
        service._quiz_service._get_correct_option_index = AsyncMock(return_value=0)

        service._count_student_answers = AsyncMock(return_value=3)  # All answered now

        result = await service.submit_answer(
            session_id=1, student_id=20, question_index=2, selected_option=0,
        )
        assert result.is_finished is True
        assert result.answered_count == 3
        assert result.total_questions == 3

    @pytest.mark.asyncio
    async def test_answer_time_is_zero(self):
        """Self-paced answers always have answer_time_ms = 0."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session()
        participant = _make_participant()

        service.repo = AsyncMock()
        service.repo.get_session = AsyncMock(return_value=session)
        service.repo.get_participant = AsyncMock(return_value=participant)
        service.repo.get_answer = AsyncMock(return_value=None)
        service.repo.add_answer = AsyncMock()
        service.repo.update_participant_score = AsyncMock()

        service._quiz_service = AsyncMock()
        service._quiz_service._check_answer = AsyncMock(return_value=True)
        service._quiz_service._get_correct_option_index = AsyncMock(return_value=0)
        service._count_student_answers = AsyncMock(return_value=1)

        await service.submit_answer(
            session_id=1, student_id=20, question_index=0, selected_option=0,
        )

        # Verify answer_time_ms=0 was passed
        call_kwargs = service.repo.add_answer.call_args
        assert call_kwargs.kwargs.get("answer_time_ms") == 0 or \
               (call_kwargs[1] if len(call_kwargs) > 1 else {}).get("answer_time_ms") == 0


class TestGetAllStudentProgress:
    """Tests for QuizSelfPacedService.get_all_student_progress."""

    @pytest.mark.asyncio
    async def test_returns_progress_for_all_participants(self):
        """Progress shows answered/total/correct per student."""
        db = AsyncMock()
        service = QuizSelfPacedService(db)
        session = _make_session(question_count=5)

        p1 = _make_participant(id=1, student_id=10, total_score=3000, correct_answers=3)
        p2 = _make_participant(id=2, student_id=11, total_score=1000, correct_answers=1)

        service.repo = AsyncMock()
        service.repo.get_participants_with_names = AsyncMock(return_value=[
            {"participant": p1, "student_name": "Alice"},
            {"participant": p2, "student_name": "Bob"},
        ])
        service.repo.get_session = AsyncMock(return_value=session)

        # p1 answered 3, p2 answered 2
        call_count = [0]
        async def mock_count(participant_id):
            call_count[0] += 1
            return 3 if participant_id == 1 else 2
        service._count_student_answers = mock_count

        result = await service.get_all_student_progress(session_id=1)
        assert len(result) == 2
        assert result[0]["student_name"] == "Alice"
        assert result[0]["answered"] == 3
        assert result[0]["total"] == 5
        assert result[0]["correct"] == 3
        assert result[1]["student_name"] == "Bob"
        assert result[1]["answered"] == 2
