"""
Homework Grading Service.

Handles:
- Auto-grading for choice questions
- AI grading for open-ended questions
- Late penalty calculation
"""
from typing import List, Tuple, Optional, TYPE_CHECKING
from datetime import datetime, timedelta

from app.models.homework import (
    Homework,
    HomeworkTaskQuestion,
    StudentTaskSubmission,
    StudentTaskAnswer,
)
from app.schemas.homework import SubmissionResult

if TYPE_CHECKING:
    from app.services.homework.ai import HomeworkAIService


class GradingServiceError(Exception):
    """Exception for grading service errors."""
    pass


class GradingService:
    """Service for answer grading and penalty calculation."""

    def __init__(self, ai_service: Optional["HomeworkAIService"] = None):
        self.ai_service = ai_service

    async def grade_answer(
        self,
        answer: StudentTaskAnswer,
        question: HomeworkTaskQuestion,
        submission: StudentTaskSubmission,
        student_id: int,
        ai_check_enabled: bool = False
    ) -> SubmissionResult:
        """
        Grade an answer based on question type.

        Args:
            answer: Student's answer
            question: Question being answered
            submission: Parent submission
            student_id: Student ID
            ai_check_enabled: Whether AI grading is enabled

        Returns:
            SubmissionResult
        """
        q_type = question.question_type

        # Store max_score locally (not in model, just for response)
        max_score = question.points

        if q_type in ("single_choice", "multiple_choice", "true_false"):
            is_correct = self._check_choice_answer(
                question=question,
                selected=answer.selected_option_ids or []
            )
            answer.is_correct = is_correct
            answer.partial_score = question.points if is_correct else 0.0

        elif q_type == "short_answer":
            is_correct = self._check_short_answer(
                question=question,
                answer_text=answer.answer_text
            )
            answer.is_correct = is_correct
            answer.partial_score = question.points if is_correct else 0.0

        elif q_type == "open_ended":
            if ai_check_enabled and self.ai_service:
                ai_result = await self.ai_service.grade_answer(
                    question=question,
                    answer_text=answer.answer_text,
                    student_id=student_id
                )
                answer.ai_score = ai_result.score
                answer.ai_confidence = ai_result.confidence
                answer.ai_feedback = ai_result.feedback
                answer.ai_rubric_scores = ai_result.rubric_scores
                answer.flagged_for_review = ai_result.confidence < 0.7
                answer.partial_score = ai_result.score * question.points
            else:
                answer.flagged_for_review = True
                answer.partial_score = 0.0

        return SubmissionResult(
            submission_id=submission.id,
            question_id=question.id,
            is_correct=answer.is_correct,
            score=answer.partial_score or 0.0,
            max_score=max_score,
            ai_feedback=answer.ai_feedback,
            ai_confidence=answer.ai_confidence,
            needs_review=answer.flagged_for_review or False
        )

    def _check_choice_answer(
        self,
        question: HomeworkTaskQuestion,
        selected: List[str]
    ) -> bool:
        """Check if selected options are correct."""
        if not question.options:
            return False

        correct_ids = {
            str(opt.get("id")) for opt in question.options
            if opt.get("is_correct")
        }
        selected_set = {str(s) for s in selected}
        return selected_set == correct_ids

    def _check_short_answer(
        self,
        question: HomeworkTaskQuestion,
        answer_text: str
    ) -> bool:
        """Check short answer (case-insensitive, trimmed)."""
        if not question.correct_answer or not answer_text:
            return False

        normalized = answer_text.strip().lower()
        correct = question.correct_answer.strip().lower()
        return normalized == correct

    def calculate_late_penalty(
        self,
        homework: Homework,
        submission_time: datetime
    ) -> Tuple[bool, float]:
        """
        Calculate late submission penalty.

        Args:
            homework: Homework object
            submission_time: Time of submission

        Returns:
            Tuple of (is_late, penalty_percent)

        Raises:
            GradingServiceError: If submission too late
        """
        if submission_time <= homework.due_date:
            return False, 0.0

        if not homework.late_submission_allowed:
            raise GradingServiceError("Late submission not allowed")

        # Grace period
        grace_deadline = homework.due_date + timedelta(
            hours=homework.grace_period_hours
        )
        if submission_time <= grace_deadline:
            return False, 0.0

        # Calculate days late
        time_late = submission_time - grace_deadline
        days_late = time_late.days + 1

        if days_late > homework.max_late_days:
            raise GradingServiceError(
                f"Submission too late (> {homework.max_late_days} days)"
            )

        penalty = min(days_late * homework.late_penalty_per_day, 100)
        return True, penalty
