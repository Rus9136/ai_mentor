"""
Student Submission Service.

Handles:
- Starting task attempts
- Submitting answers
- Completing submissions
- Managing student homework status
"""
import logging
from typing import Optional, List, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    StudentTaskSubmission,
    HomeworkStatus,
    HomeworkStudentStatus,
    TaskSubmissionStatus,
)
from app.repositories.homework import HomeworkRepository
from app.schemas.homework import SubmissionResult, TaskSubmissionResult, SubmissionStatus
from app.services.homework.grading_service import GradingService, GradingServiceError

logger = logging.getLogger(__name__)


class SubmissionServiceError(Exception):
    """Exception for submission service errors."""
    pass


class SubmissionService:
    """Service for managing student homework submissions."""

    def __init__(
        self,
        db: AsyncSession,
        grading_service: Optional[GradingService] = None
    ):
        self.db = db
        self.repo = HomeworkRepository(db)
        self.grading = grading_service or GradingService()

    async def get_student_homework(
        self,
        homework_id: int,
        student_id: int
    ) -> Optional[HomeworkStudent]:
        """Get student's homework assignment."""
        return await self.repo.get_student_homework(
            homework_id=homework_id,
            student_id=student_id
        )

    async def list_student_homework(
        self,
        student_id: int,
        school_id: int,
        status: Optional[HomeworkStudentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HomeworkStudent], int]:
        """List homework assigned to student with pagination."""
        return await self.repo.list_student_homework(
            student_id=student_id,
            school_id=school_id,
            status=status,
            page=page,
            page_size=page_size,
        )

    async def start_task(
        self,
        homework_id: int,
        task_id: int,
        student_id: int
    ) -> StudentTaskSubmission:
        """
        Start a task attempt.

        Args:
            homework_id: Homework ID
            task_id: Task ID
            student_id: Student ID

        Returns:
            Created StudentTaskSubmission

        Raises:
            SubmissionServiceError: If max attempts exceeded or not assigned
        """
        hw_student = await self.get_student_homework(homework_id, student_id)
        if not hw_student:
            raise SubmissionServiceError("Homework not assigned to student")

        homework = await self.repo.get_by_id(
            homework_id=homework_id,
            school_id=hw_student.school_id,
            load_tasks=False
        )

        if not homework:
            raise SubmissionServiceError("Homework not found")

        if homework.status == HomeworkStatus.CLOSED:
            raise SubmissionServiceError("Homework is closed")

        if homework.status == HomeworkStatus.DRAFT:
            raise SubmissionServiceError("Homework is not published yet")

        task = await self.repo.get_task_by_id(
            task_id=task_id,
            school_id=homework.school_id,
            load_questions=False
        )
        if not task or task.homework_id != homework_id:
            raise SubmissionServiceError("Task not found in this homework")

        attempts_used = await self.repo.get_attempts_count(
            homework_student_id=hw_student.id,
            task_id=task_id
        )

        if attempts_used >= task.max_attempts:
            raise SubmissionServiceError(
                f"Maximum attempts ({task.max_attempts}) reached"
            )

        # Calculate late status
        is_late = False
        late_penalty = 0.0
        now = datetime.now(timezone.utc)

        if now > homework.due_date:
            try:
                is_late, late_penalty = self.grading.calculate_late_penalty(
                    homework=homework,
                    submission_time=now
                )
            except GradingServiceError as e:
                raise SubmissionServiceError(str(e))

        submission = await self.repo.create_submission(
            homework_student_id=hw_student.id,
            task_id=task_id,
            student_id=student_id,
            school_id=hw_student.school_id,
            attempt_number=attempts_used + 1
        )

        # Update student status if first task
        if hw_student.status == HomeworkStudentStatus.ASSIGNED:
            await self.repo.update_student_homework_status(
                homework_student_id=hw_student.id,
                status=HomeworkStudentStatus.IN_PROGRESS
            )

        return submission

    async def submit_answer(
        self,
        submission_id: int,
        question_id: int,
        answer_text: str,
        selected_options: Optional[List[str]] = None,
        student_id: int = None
    ) -> SubmissionResult:
        """
        Submit an answer for a question.

        Args:
            submission_id: Submission ID
            question_id: Question ID
            answer_text: Answer text
            selected_options: Selected option IDs (for choice questions)
            student_id: Student ID (for AI grading)

        Returns:
            SubmissionResult with score and feedback
        """
        submission = await self.repo.get_submission_by_id(submission_id)
        if not submission:
            raise SubmissionServiceError("Submission not found")

        if submission.status != TaskSubmissionStatus.IN_PROGRESS:
            raise SubmissionServiceError("Submission is not in progress")

        question = await self.db.get(HomeworkTaskQuestion, question_id)
        if not question or question.homework_task_id != submission.homework_task_id:
            raise SubmissionServiceError("Question not found in this task")

        answer = await self.repo.save_answer(
            submission_id=submission_id,
            question_id=question_id,
            student_id=student_id,
            school_id=submission.school_id,
            answer_text=answer_text,
            selected_options=selected_options
        )

        # Get homework for AI check setting
        # Use homework_student_id to avoid lazy loading on submission.homework_student
        hw_student = await self.db.get(HomeworkStudent, submission.homework_student_id)
        ai_enabled = False
        if hw_student:
            # Get homework to check ai_check_enabled
            homework = await self.db.get(Homework, hw_student.homework_id)
            ai_enabled = homework.ai_check_enabled if homework else False

        result = await self.grading.grade_answer(
            answer=answer,
            question=question,
            submission=submission,
            student_id=student_id,
            ai_check_enabled=ai_enabled
        )

        await self.db.flush()
        return result

    async def complete_submission(
        self,
        submission_id: int,
        student_id: int
    ) -> TaskSubmissionResult:
        """
        Complete a task submission.

        Args:
            submission_id: Submission ID
            student_id: Student ID

        Returns:
            TaskSubmissionResult with total score
        """
        submission = await self.repo.get_submission_by_id(
            submission_id, load_answers=True
        )
        if not submission:
            raise SubmissionServiceError("Submission not found")

        # Use submission.student_id directly instead of lazy loading homework_student
        if submission.student_id != student_id:
            raise SubmissionServiceError("Not authorized")

        if submission.status != TaskSubmissionStatus.IN_PROGRESS:
            raise SubmissionServiceError("Submission is not in progress")

        total_score = 0.0
        max_score = 0.0
        needs_review = False

        for answer in submission.answers:
            total_score += answer.partial_score or 0.0
            # Get question to find max_score (question.points)
            question = await self.db.get(HomeworkTaskQuestion, answer.question_id)
            if question:
                max_score += question.points
            if answer.flagged_for_review:
                needs_review = True

        original_score = total_score
        if submission.is_late and submission.late_penalty_applied > 0:
            penalty_factor = 1 - (submission.late_penalty_applied / 100)
            total_score = total_score * penalty_factor
            submission.original_score = original_score

        submission.score = total_score
        submission.max_score = max_score
        submission.status = (
            TaskSubmissionStatus.NEEDS_REVIEW if needs_review
            else TaskSubmissionStatus.GRADED
        )
        submission.completed_at = datetime.now(timezone.utc)

        await self.db.flush()

        # Calculate percentage
        percentage = (total_score / max_score * 100) if max_score > 0 else 0.0

        # Count correct/incorrect
        correct_count = sum(1 for a in submission.answers if a.is_correct)
        incorrect_count = len(submission.answers) - correct_count

        return TaskSubmissionResult(
            submission_id=submission_id,
            task_id=submission.homework_task_id,
            status=SubmissionStatus(submission.status.value),
            attempt_number=submission.attempt_number,
            total_score=total_score,
            max_score=max_score,
            percentage=percentage,
            is_late=submission.is_late or False,
            late_penalty_applied=submission.late_penalty_applied or 0,
            original_score=original_score if submission.is_late else None,
            correct_count=correct_count,
            incorrect_count=incorrect_count
        )
