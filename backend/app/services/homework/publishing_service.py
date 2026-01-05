"""
Homework Publishing Service.

Handles:
- Publishing homework to students
- Closing homework submissions
"""
import logging
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import Homework, HomeworkStatus
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

        # Validate all tasks have questions
        for task in homework.tasks:
            if not task.questions:
                raise PublishingServiceError(
                    f"Task '{task.paragraph_id}' has no questions"
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
