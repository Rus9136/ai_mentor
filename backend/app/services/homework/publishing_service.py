"""
Homework Publishing Service.

Handles:
- Publishing homework to students
- Closing homework submissions
"""
import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import Homework, HomeworkStatus, HomeworkTaskType
from app.repositories.homework import HomeworkRepository
from app.repositories.school_class_repo import SchoolClassRepository

logger = logging.getLogger(__name__)


class PublishingServiceError(Exception):
    """Exception for publishing service errors."""
    pass


class PublishingService:
    """Service for homework publishing and lifecycle management."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HomeworkRepository(db)
        self.class_repo = SchoolClassRepository(db)

    async def publish_homework(
        self,
        homework_id: int,
        school_id: int,
        student_ids: Optional[List[int]] = None
    ) -> Homework:
        """
        Publish homework and assign to students.

        Args:
            homework_id: Homework ID
            school_id: School ID
            student_ids: Optional list of student IDs.
                        If None, assigns to all students in class.

        Returns:
            Published Homework

        Raises:
            PublishingServiceError: If homework cannot be published
        """
        homework = await self.repo.get_by_id(
            homework_id, school_id, load_tasks=True, load_questions=True
        )
        if not homework:
            raise PublishingServiceError("Homework not found")

        if homework.status != HomeworkStatus.DRAFT:
            raise PublishingServiceError("Can only publish draft homework")

        if not homework.tasks:
            raise PublishingServiceError("Homework must have at least one task")

        # Validate all tasks have required content based on task type
        validation_errors = self._validate_tasks_content(homework.tasks)
        if validation_errors:
            raise PublishingServiceError(
                f"Invalid tasks: {'; '.join(validation_errors)}"
            )

        # Get students to assign
        if student_ids is None:
            students = await self.class_repo.get_students(
                class_id=homework.class_id,
                school_id=school_id
            )
            student_ids = [s.id for s in students]

        if not student_ids:
            raise PublishingServiceError("No students to assign homework to")

        logger.info(
            f"Publishing homework {homework_id} to {len(student_ids)} students"
        )

        # Assign to students
        await self.repo.assign_to_students(
            homework_id=homework_id,
            school_id=school_id,
            student_ids=student_ids
        )

        # Update status
        homework = await self.repo.update_status(
            homework_id=homework_id,
            school_id=school_id,
            status=HomeworkStatus.PUBLISHED
        )

        return homework

    def _validate_tasks_content(self, tasks) -> List[str]:
        """
        Validate that tasks have required content based on their type.

        Rules:
        - READ: valid if has paragraph_id OR has questions
        - QUIZ, OPEN_QUESTION, PRACTICE, CODE: must have questions
        - ESSAY: valid if has questions OR instructions

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        for task in tasks:
            has_questions = task.questions and len(task.questions) > 0

            if task.task_type == HomeworkTaskType.READ:
                # READ is valid if has paragraph to read OR has questions
                if not task.paragraph_id and not has_questions:
                    errors.append(
                        f"READ task (ID:{task.id}) needs paragraph_id or questions"
                    )

            elif task.task_type in [
                HomeworkTaskType.QUIZ,
                HomeworkTaskType.OPEN_QUESTION,
                HomeworkTaskType.PRACTICE,
                HomeworkTaskType.CODE,
            ]:
                # These types must have questions
                if not has_questions:
                    errors.append(
                        f"{task.task_type.value.upper()} task (ID:{task.id}) must have questions"
                    )

            elif task.task_type == HomeworkTaskType.ESSAY:
                # ESSAY can have just instructions without questions
                if not has_questions and not task.instructions:
                    errors.append(
                        f"ESSAY task (ID:{task.id}) needs questions or instructions"
                    )

        return errors

    async def close_homework(
        self,
        homework_id: int,
        school_id: int
    ) -> Homework:
        """
        Close homework for submissions.

        Args:
            homework_id: Homework ID
            school_id: School ID

        Returns:
            Closed Homework
        """
        homework = await self.repo.get_by_id(homework_id, school_id, load_tasks=False)
        if not homework:
            raise PublishingServiceError("Homework not found")

        if homework.status != HomeworkStatus.PUBLISHED:
            raise PublishingServiceError("Can only close published homework")

        return await self.repo.update_status(
            homework_id=homework_id,
            school_id=school_id,
            status=HomeworkStatus.CLOSED
        )
