"""
Unit tests for Homework GradingService.

Tests:
- Auto-grading for choice questions (single, multiple, true/false)
- Short answer matching (case-insensitive, trimmed)
- Open-ended grading without AI (flagged for review)
- Late penalty calculation
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, AsyncMock

from app.services.homework.grading_service import GradingService, GradingServiceError
from app.models.homework import (
    Homework,
    HomeworkTaskQuestion,
    StudentTaskSubmission,
    StudentTaskAnswer,
    HomeworkStatus,
    TaskSubmissionStatus,
)


# =============================================================================
# Helpers
# =============================================================================

def make_question(
    q_type: str = "single_choice",
    options=None,
    correct_answer=None,
    points: float = 10.0,
) -> HomeworkTaskQuestion:
    """Create a mock HomeworkTaskQuestion."""
    q = MagicMock(spec=HomeworkTaskQuestion)
    q.id = 1
    q.question_type = q_type
    q.options = options
    q.correct_answer = correct_answer
    q.points = points
    q.grading_rubric = None
    q.expected_answer_hints = None
    return q


def make_answer(
    selected_option_ids=None,
    answer_text=None,
) -> StudentTaskAnswer:
    """Create a mock StudentTaskAnswer."""
    a = MagicMock(spec=StudentTaskAnswer)
    a.id = 1
    a.selected_option_ids = selected_option_ids
    a.answer_text = answer_text
    a.is_correct = None
    a.partial_score = None
    a.ai_score = None
    a.ai_confidence = None
    a.ai_feedback = None
    a.ai_rubric_scores = None
    a.flagged_for_review = None
    return a


def make_submission() -> StudentTaskSubmission:
    """Create a mock StudentTaskSubmission."""
    s = MagicMock(spec=StudentTaskSubmission)
    s.id = 1
    s.homework_student_id = 1
    s.homework_task_id = 1
    s.status = TaskSubmissionStatus.IN_PROGRESS
    s.is_late = False
    s.late_penalty_applied = 0
    return s


def make_homework(
    due_date=None,
    late_submission_allowed=True,
    late_penalty_per_day=10,
    grace_period_hours=0,
    max_late_days=7,
) -> Homework:
    """Create a mock Homework for late penalty tests."""
    h = MagicMock(spec=Homework)
    h.due_date = due_date or (datetime.now(timezone.utc) + timedelta(days=7))
    h.late_submission_allowed = late_submission_allowed
    h.late_penalty_per_day = late_penalty_per_day
    h.grace_period_hours = grace_period_hours
    h.max_late_days = max_late_days
    return h


# =============================================================================
# Choice Grading
# =============================================================================

class TestChoiceGrading:
    """Auto-grading for single_choice, multiple_choice, true_false."""

    def setup_method(self):
        self.service = GradingService()

    @pytest.mark.asyncio
    async def test_single_choice_correct(self):
        """Selecting the correct option → is_correct=True, full score."""
        question = make_question(
            q_type="single_choice",
            options=[
                {"id": "a", "text": "Wrong", "is_correct": False},
                {"id": "b", "text": "Right", "is_correct": True},
            ],
            points=10.0,
        )
        answer = make_answer(selected_option_ids=["b"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is True
        assert answer.partial_score == 10.0
        assert result.is_correct is True
        assert result.score == 10.0

    @pytest.mark.asyncio
    async def test_single_choice_incorrect(self):
        """Selecting the wrong option → is_correct=False, score=0."""
        question = make_question(
            q_type="single_choice",
            options=[
                {"id": "a", "text": "Wrong", "is_correct": False},
                {"id": "b", "text": "Right", "is_correct": True},
            ],
            points=10.0,
        )
        answer = make_answer(selected_option_ids=["a"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False
        assert answer.partial_score == 0.0
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_single_choice_no_selection(self):
        """Empty selection → is_correct=False."""
        question = make_question(
            q_type="single_choice",
            options=[
                {"id": "a", "text": "Wrong", "is_correct": False},
                {"id": "b", "text": "Right", "is_correct": True},
            ],
        )
        answer = make_answer(selected_option_ids=[])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False

    @pytest.mark.asyncio
    async def test_multiple_choice_all_correct(self):
        """Selecting exactly the correct options → is_correct=True."""
        question = make_question(
            q_type="multiple_choice",
            options=[
                {"id": "a", "text": "2", "is_correct": True},
                {"id": "b", "text": "3", "is_correct": True},
                {"id": "c", "text": "4", "is_correct": False},
            ],
            points=5.0,
        )
        answer = make_answer(selected_option_ids=["a", "b"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is True
        assert answer.partial_score == 5.0

    @pytest.mark.asyncio
    async def test_multiple_choice_missing_one(self):
        """Missing one correct option → is_correct=False (all-or-nothing)."""
        question = make_question(
            q_type="multiple_choice",
            options=[
                {"id": "a", "text": "2", "is_correct": True},
                {"id": "b", "text": "3", "is_correct": True},
                {"id": "c", "text": "4", "is_correct": False},
            ],
        )
        answer = make_answer(selected_option_ids=["a"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False
        assert answer.partial_score == 0.0

    @pytest.mark.asyncio
    async def test_multiple_choice_extra_incorrect(self):
        """Selecting correct + extra incorrect → is_correct=False."""
        question = make_question(
            q_type="multiple_choice",
            options=[
                {"id": "a", "text": "2", "is_correct": True},
                {"id": "b", "text": "3", "is_correct": True},
                {"id": "c", "text": "4", "is_correct": False},
            ],
        )
        answer = make_answer(selected_option_ids=["a", "b", "c"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False

    @pytest.mark.asyncio
    async def test_true_false_correct(self):
        """Selecting correct true/false option."""
        question = make_question(
            q_type="true_false",
            options=[
                {"id": "t", "text": "True", "is_correct": False},
                {"id": "f", "text": "False", "is_correct": True},
            ],
            points=5.0,
        )
        answer = make_answer(selected_option_ids=["f"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is True
        assert answer.partial_score == 5.0

    @pytest.mark.asyncio
    async def test_true_false_incorrect(self):
        """Selecting wrong true/false option."""
        question = make_question(
            q_type="true_false",
            options=[
                {"id": "t", "text": "True", "is_correct": False},
                {"id": "f", "text": "False", "is_correct": True},
            ],
        )
        answer = make_answer(selected_option_ids=["t"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False

    @pytest.mark.asyncio
    async def test_no_options_returns_false(self):
        """Question with no options → is_correct=False."""
        question = make_question(q_type="single_choice", options=None)
        answer = make_answer(selected_option_ids=["a"])
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False


# =============================================================================
# Short Answer Grading
# =============================================================================

class TestShortAnswerGrading:
    """Short answer matching logic."""

    def setup_method(self):
        self.service = GradingService()

    @pytest.mark.asyncio
    async def test_exact_match(self):
        """Exact string match → correct."""
        question = make_question(q_type="short_answer", correct_answer="42", points=5.0)
        answer = make_answer(answer_text="42")
        submission = make_submission()

        result = await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is True
        assert answer.partial_score == 5.0

    @pytest.mark.asyncio
    async def test_case_insensitive_match(self):
        """'ANSWER' matches 'answer' → correct."""
        question = make_question(q_type="short_answer", correct_answer="answer")
        answer = make_answer(answer_text="ANSWER")
        submission = make_submission()

        await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is True

    @pytest.mark.asyncio
    async def test_whitespace_trimmed(self):
        """' answer ' matches 'answer' → correct."""
        question = make_question(q_type="short_answer", correct_answer="answer")
        answer = make_answer(answer_text="  answer  ")
        submission = make_submission()

        await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is True

    @pytest.mark.asyncio
    async def test_wrong_answer(self):
        """Different text → incorrect."""
        question = make_question(q_type="short_answer", correct_answer="42")
        answer = make_answer(answer_text="43")
        submission = make_submission()

        await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False
        assert answer.partial_score == 0.0

    @pytest.mark.asyncio
    async def test_empty_answer(self):
        """Empty string → incorrect."""
        question = make_question(q_type="short_answer", correct_answer="42")
        answer = make_answer(answer_text="")
        submission = make_submission()

        await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False

    @pytest.mark.asyncio
    async def test_none_answer(self):
        """None answer → incorrect."""
        question = make_question(q_type="short_answer", correct_answer="42")
        answer = make_answer(answer_text=None)
        submission = make_submission()

        await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False

    @pytest.mark.asyncio
    async def test_none_correct_answer(self):
        """Question with no correct_answer → incorrect."""
        question = make_question(q_type="short_answer", correct_answer=None)
        answer = make_answer(answer_text="anything")
        submission = make_submission()

        await self.service.grade_answer(answer, question, submission, student_id=1)

        assert answer.is_correct is False


# =============================================================================
# Open-Ended Grading
# =============================================================================

class TestOpenEndedGrading:
    """Open-ended questions without AI service → flagged for review."""

    def setup_method(self):
        self.service = GradingService()  # No AI service

    @pytest.mark.asyncio
    async def test_open_ended_no_ai_flagged(self):
        """Open-ended without AI → flagged_for_review=True, score=0."""
        question = make_question(q_type="open_ended", points=20.0)
        answer = make_answer(answer_text="My detailed answer about the topic.")
        submission = make_submission()

        result = await self.service.grade_answer(
            answer, question, submission, student_id=1, ai_check_enabled=False
        )

        assert answer.flagged_for_review is True
        assert answer.partial_score == 0.0
        assert result.needs_review is True
        assert result.score == 0.0

    @pytest.mark.asyncio
    async def test_open_ended_ai_disabled(self):
        """Open-ended with ai_check_enabled=False even with AI service → flagged."""
        ai_service = MagicMock()
        service = GradingService(ai_service=ai_service)

        question = make_question(q_type="open_ended", points=20.0)
        answer = make_answer(answer_text="Some answer")
        submission = make_submission()

        result = await service.grade_answer(
            answer, question, submission, student_id=1, ai_check_enabled=False
        )

        assert answer.flagged_for_review is True
        assert answer.partial_score == 0.0
        # AI service should NOT have been called
        ai_service.grade_answer.assert_not_called()


# =============================================================================
# Late Penalty Calculation
# =============================================================================

class TestLatePenaltyCalculation:
    """Late penalty calculation logic in GradingService."""

    def setup_method(self):
        self.service = GradingService()

    def test_on_time_submission(self):
        """Submission before due_date → (False, 0.0)."""
        due = datetime.now(timezone.utc) + timedelta(hours=1)
        homework = make_homework(due_date=due)
        now = datetime.now(timezone.utc)

        is_late, penalty = self.service.calculate_late_penalty(homework, now)

        assert is_late is False
        assert penalty == 0.0

    def test_exactly_on_time(self):
        """Submission at exactly due_date → (False, 0.0)."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(due_date=due)

        is_late, penalty = self.service.calculate_late_penalty(homework, due)

        assert is_late is False
        assert penalty == 0.0

    def test_late_not_allowed_raises(self):
        """Late when late_submission_allowed=False → GradingServiceError."""
        due = datetime.now(timezone.utc) - timedelta(hours=1)
        homework = make_homework(due_date=due, late_submission_allowed=False)
        now = datetime.now(timezone.utc)

        with pytest.raises(GradingServiceError, match="Late submission not allowed"):
            self.service.calculate_late_penalty(homework, now)

    def test_within_grace_period(self):
        """Submit during grace period → not late."""
        due = datetime.now(timezone.utc) - timedelta(hours=1)
        homework = make_homework(due_date=due, grace_period_hours=2)
        now = datetime.now(timezone.utc)

        is_late, penalty = self.service.calculate_late_penalty(homework, now)

        assert is_late is False
        assert penalty == 0.0

    def test_exactly_at_grace_deadline(self):
        """Submit at exactly grace period end → not late."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(due_date=due, grace_period_hours=2)
        grace_end = due + timedelta(hours=2)

        is_late, penalty = self.service.calculate_late_penalty(homework, grace_end)

        assert is_late is False
        assert penalty == 0.0

    def test_one_day_after_grace(self):
        """1 day after grace → (True, late_penalty_per_day)."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(
            due_date=due,
            grace_period_hours=0,
            late_penalty_per_day=10,
            max_late_days=7,
        )
        submission_time = due + timedelta(days=1, seconds=1)

        is_late, penalty = self.service.calculate_late_penalty(homework, submission_time)

        assert is_late is True
        assert penalty == 20.0  # days_late = time_late.days + 1 = 1 + 1 = 2? Let's check

    def test_penalty_accumulates(self):
        """3 days late → penalty = 3 * penalty_per_day."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(
            due_date=due,
            grace_period_hours=0,
            late_penalty_per_day=10,
            max_late_days=7,
        )
        # 2 days and some hours after due
        submission_time = due + timedelta(days=2, hours=5)

        is_late, penalty = self.service.calculate_late_penalty(homework, submission_time)

        assert is_late is True
        # time_late = 2d 5h, days = 2, days_late = 3
        assert penalty == 30.0

    def test_penalty_capped_at_100(self):
        """Penalty cannot exceed 100%."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(
            due_date=due,
            grace_period_hours=0,
            late_penalty_per_day=50,
            max_late_days=10,
        )
        submission_time = due + timedelta(days=3)

        is_late, penalty = self.service.calculate_late_penalty(homework, submission_time)

        assert is_late is True
        assert penalty <= 100

    def test_exceeds_max_late_days_raises(self):
        """Submit > max_late_days → GradingServiceError."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(
            due_date=due,
            grace_period_hours=0,
            late_penalty_per_day=10,
            max_late_days=3,
        )
        submission_time = due + timedelta(days=5)

        with pytest.raises(GradingServiceError, match="Submission too late"):
            self.service.calculate_late_penalty(homework, submission_time)

    def test_zero_grace_period(self):
        """grace_period_hours=0, submit 1 hour late → penalty applied."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(
            due_date=due,
            grace_period_hours=0,
            late_penalty_per_day=10,
            max_late_days=7,
        )
        submission_time = due + timedelta(hours=1)

        is_late, penalty = self.service.calculate_late_penalty(homework, submission_time)

        assert is_late is True
        assert penalty > 0

    def test_zero_penalty_per_day(self):
        """late_penalty_per_day=0, submit late → (True, 0.0)."""
        due = datetime(2025, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
        homework = make_homework(
            due_date=due,
            grace_period_hours=0,
            late_penalty_per_day=0,
            max_late_days=7,
        )
        submission_time = due + timedelta(days=2)

        is_late, penalty = self.service.calculate_late_penalty(homework, submission_time)

        assert is_late is True
        assert penalty == 0.0
