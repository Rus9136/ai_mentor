"""
Homework services package.

Provides modular service classes and a facade for backward compatibility.
"""
from typing import Optional, List, Tuple, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    StudentTaskSubmission,
    StudentTaskAnswer,
    HomeworkStatus,
    HomeworkStudentStatus,
)
from app.schemas.homework import (
    GenerationParams,
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkTaskCreate,
    QuestionCreate,
    SubmissionResult,
    TaskSubmissionResult,
)

from app.services.homework.homework_service import (
    HomeworkService as CoreHomeworkService,
    HomeworkServiceError,
)
from app.services.homework.publishing_service import (
    PublishingService,
    PublishingServiceError,
)
from app.services.homework.submission_service import (
    SubmissionService,
    SubmissionServiceError,
)
from app.services.homework.grading_service import (
    GradingService,
    GradingServiceError,
)
from app.services.homework.review_service import ReviewService
from app.services.homework.ai_orchestration_service import (
    AIOrchestrationService,
    AIOrchestrationError,
)

if TYPE_CHECKING:
    from app.services.homework.ai import HomeworkAIService


class HomeworkService:
    """
    Facade service that delegates to specialized services.

    Provides backward compatibility while internally using modular services.
    """

    def __init__(
        self,
        db: AsyncSession,
        ai_service: Optional["HomeworkAIService"] = None
    ):
        self.db = db
        self.ai_service = ai_service

        # Initialize specialized services
        self._core = CoreHomeworkService(db)
        self._publishing = PublishingService(db)
        self._grading = GradingService(ai_service)
        self._submission = SubmissionService(db, self._grading)
        self._review = ReviewService(db)
        self._ai_orchestration = (
            AIOrchestrationService(db, ai_service) if ai_service else None
        )

        # Expose repo for direct access where needed
        self.homework_repo = self._core.repo

    # =========================================================================
    # Homework CRUD (delegates to CoreHomeworkService)
    # =========================================================================

    async def create_homework(
        self,
        data: HomeworkCreate,
        school_id: int,
        teacher_id: int
    ) -> Homework:
        return await self._core.create_homework(data, school_id, teacher_id)

    async def get_homework(
        self,
        homework_id: int,
        school_id: int,
        load_tasks: bool = True,
        load_questions: bool = True
    ) -> Optional[Homework]:
        return await self._core.get_homework(
            homework_id, school_id, load_tasks, load_questions
        )

    async def update_homework(
        self,
        homework_id: int,
        data: HomeworkUpdate,
        school_id: int
    ) -> Optional[Homework]:
        return await self._core.update_homework(homework_id, data, school_id)

    async def delete_homework(
        self,
        homework_id: int,
        school_id: int,
        teacher_id: int
    ) -> bool:
        return await self._core.delete_homework(homework_id, school_id, teacher_id)

    async def list_homework_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None,
        class_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Homework]:
        return await self._core.list_homework_by_teacher(
            teacher_id, school_id, status, class_id, skip, limit
        )

    async def list_homework_by_class(
        self,
        class_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None
    ) -> List[Homework]:
        return await self._core.list_homework_by_class(class_id, school_id, status)

    # =========================================================================
    # Tasks (delegates to CoreHomeworkService)
    # =========================================================================

    async def add_task(
        self,
        homework_id: int,
        data: HomeworkTaskCreate,
        school_id: int
    ) -> HomeworkTask:
        return await self._core.add_task(homework_id, data, school_id)

    async def get_task(
        self,
        task_id: int,
        school_id: int,
        load_questions: bool = True
    ) -> Optional[HomeworkTask]:
        return await self._core.get_task(task_id, school_id, load_questions)

    async def delete_task(self, task_id: int, school_id: int) -> bool:
        return await self._core.delete_task(task_id, school_id)

    # =========================================================================
    # Questions (delegates to CoreHomeworkService)
    # =========================================================================

    async def add_question(
        self,
        task_id: int,
        school_id: int,
        data: QuestionCreate
    ) -> HomeworkTaskQuestion:
        return await self._core.add_question(task_id, school_id, data)

    async def add_questions_batch(
        self,
        task_id: int,
        school_id: int,
        questions: List[QuestionCreate]
    ) -> List[HomeworkTaskQuestion]:
        return await self._core.add_questions_batch(task_id, school_id, questions)

    async def replace_question(
        self,
        question_id: int,
        new_data: QuestionCreate
    ) -> HomeworkTaskQuestion:
        return await self._core.replace_question(question_id, new_data)

    # =========================================================================
    # Publishing (delegates to PublishingService)
    # =========================================================================

    async def publish_homework(
        self,
        homework_id: int,
        school_id: int,
        student_ids: Optional[List[int]] = None
    ) -> Homework:
        return await self._publishing.publish_homework(
            homework_id, school_id, student_ids
        )

    async def close_homework(
        self,
        homework_id: int,
        school_id: int
    ) -> Homework:
        return await self._publishing.close_homework(homework_id, school_id)

    # =========================================================================
    # Submissions (delegates to SubmissionService)
    # =========================================================================

    async def get_student_homework(
        self,
        homework_id: int,
        student_id: int
    ) -> Optional[HomeworkStudent]:
        return await self._submission.get_student_homework(homework_id, student_id)

    async def list_student_homework(
        self,
        student_id: int,
        school_id: int,
        status: Optional[HomeworkStudentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HomeworkStudent], int]:
        return await self._submission.list_student_homework(
            student_id, school_id, status, page, page_size
        )

    async def start_task(
        self,
        homework_id: int,
        task_id: int,
        student_id: int
    ) -> StudentTaskSubmission:
        try:
            return await self._submission.start_task(homework_id, task_id, student_id)
        except SubmissionServiceError as e:
            raise HomeworkServiceError(str(e)) from e

    async def submit_answer(
        self,
        submission_id: int,
        question_id: int,
        answer_text: str,
        selected_options: Optional[List[str]] = None,
        student_id: int = None
    ) -> SubmissionResult:
        try:
            return await self._submission.submit_answer(
                submission_id, question_id, answer_text, selected_options, student_id
            )
        except SubmissionServiceError as e:
            raise HomeworkServiceError(str(e)) from e

    async def complete_submission(
        self,
        submission_id: int,
        student_id: int
    ) -> TaskSubmissionResult:
        try:
            return await self._submission.complete_submission(submission_id, student_id)
        except SubmissionServiceError as e:
            raise HomeworkServiceError(str(e)) from e

    # =========================================================================
    # Grading (delegates to GradingService via SubmissionService)
    # =========================================================================

    async def calculate_late_penalty(self, homework: Homework, submission_time):
        return self._grading.calculate_late_penalty(homework, submission_time)

    # =========================================================================
    # Review (delegates to ReviewService)
    # =========================================================================

    async def get_answers_for_review(
        self,
        school_id: int,
        homework_id: Optional[int] = None,
        limit: int = 50
    ) -> List[StudentTaskAnswer]:
        return await self._review.get_answers_for_review(
            school_id, homework_id, limit
        )

    async def review_answer(
        self,
        answer_id: int,
        teacher_id: int,
        score: float,
        feedback: Optional[str] = None
    ) -> StudentTaskAnswer:
        return await self._review.review_answer(
            answer_id, teacher_id, score, feedback
        )

    # =========================================================================
    # AI Generation (delegates to AIOrchestrationService)
    # =========================================================================

    async def generate_questions_for_task(
        self,
        task_id: int,
        school_id: int,
        regenerate: bool = False,
        params: Optional["GenerationParams"] = None
    ) -> List[HomeworkTaskQuestion]:
        if not self._ai_orchestration:
            raise HomeworkServiceError("AI service not configured")
        return await self._ai_orchestration.generate_questions_for_task(
            task_id, school_id, regenerate, params
        )

    # =========================================================================
    # Statistics (delegates to CoreHomeworkService)
    # =========================================================================

    async def get_homework_stats(self, homework_id: int, school_id: int) -> dict:
        return await self._core.get_homework_stats(homework_id, school_id)


__all__ = [
    # Facade
    "HomeworkService",
    "HomeworkServiceError",
    # Specialized services
    "CoreHomeworkService",
    "PublishingService",
    "PublishingServiceError",
    "SubmissionService",
    "SubmissionServiceError",
    "GradingService",
    "GradingServiceError",
    "ReviewService",
    "AIOrchestrationService",
    "AIOrchestrationError",
]
