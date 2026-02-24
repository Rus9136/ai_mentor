"""
Core Homework Service for CRUD operations.

Handles:
- Homework CRUD with validation
- Task and question management
- List operations
"""
import logging
from typing import Optional, List, Dict

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStatus,
)
from app.repositories.homework import HomeworkRepository
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkTaskCreate,
    QuestionCreate,
)

logger = logging.getLogger(__name__)


class HomeworkServiceError(Exception):
    """Exception for homework service errors."""
    pass


class HomeworkService:
    """
    Core service for homework CRUD operations.

    Handles:
    - Homework CRUD with validation
    - Task management
    - Question management
    - List operations
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HomeworkRepository(db)

    # =========================================================================
    # Homework CRUD
    # =========================================================================

    async def create_homework(
        self,
        data: HomeworkCreate,
        school_id: int,
        teacher_id: int
    ) -> Homework:
        """Create a new homework assignment (draft)."""
        logger.info(
            f"Creating homework: title='{data.title}', "
            f"class_id={data.class_id}, teacher_id={teacher_id}"
        )

        homework = await self.repo.create(
            data=data.model_dump(exclude={"tasks"}, exclude_unset=False),
            school_id=school_id,
            teacher_id=teacher_id
        )

        tasks = getattr(data, 'tasks', None)
        if tasks:
            for task_data in tasks:
                await self.add_task(
                    homework_id=homework.id,
                    data=task_data,
                    school_id=school_id
                )

        return homework

    async def get_homework(
        self,
        homework_id: int,
        school_id: int,
        load_tasks: bool = True,
        load_questions: bool = True
    ) -> Optional[Homework]:
        """Get homework by ID."""
        return await self.repo.get_by_id(
            homework_id=homework_id,
            school_id=school_id,
            load_tasks=load_tasks,
            load_questions=load_questions
        )

    async def update_homework(
        self,
        homework_id: int,
        data: HomeworkUpdate,
        school_id: int
    ) -> Optional[Homework]:
        """Update homework (only in DRAFT status)."""
        homework = await self.get_homework(homework_id, school_id, load_tasks=False)
        if not homework:
            return None

        if homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError("Cannot modify homework after publishing")

        return await self.repo.update(
            homework_id=homework_id,
            school_id=school_id,
            data=data.model_dump(exclude_unset=True)
        )

    async def delete_homework(
        self,
        homework_id: int,
        school_id: int,
        teacher_id: int
    ) -> bool:
        """Delete homework (only in DRAFT status)."""
        homework = await self.get_homework(homework_id, school_id, load_tasks=False)
        if not homework:
            raise HomeworkServiceError("Homework not found")

        if homework.teacher_id != teacher_id:
            raise HomeworkServiceError("You can only delete your own homework")

        if homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError("Can only delete homework in DRAFT status")

        return await self.repo.soft_delete(homework_id, school_id)

    async def list_homework_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None,
        class_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 50
    ) -> List[Homework]:
        """List homework created by teacher."""
        return await self.repo.list_by_teacher(
            teacher_id=teacher_id,
            school_id=school_id,
            status=status,
            class_id=class_id,
            offset=skip,
            limit=limit
        )

    async def list_homework_by_class(
        self,
        class_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None
    ) -> List[Homework]:
        """List homework for a class."""
        return await self.repo.list_by_class(
            class_id=class_id,
            school_id=school_id,
            status=status
        )

    # =========================================================================
    # Tasks
    # =========================================================================

    async def add_task(
        self,
        homework_id: int,
        data: HomeworkTaskCreate,
        school_id: int
    ) -> HomeworkTask:
        """Add a task to homework."""
        homework = await self.get_homework(homework_id, school_id, load_tasks=False)
        if not homework:
            raise HomeworkServiceError("Homework not found")

        if homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError("Cannot add tasks to published homework")

        task_data = data.model_dump()

        # If exercise_id is provided, validate it and auto-fill paragraph_id
        if task_data.get("exercise_id"):
            from app.repositories.exercise_repo import ExerciseRepository
            exercise_repo = ExerciseRepository(self.db)
            exercise = await exercise_repo.get_by_id(task_data["exercise_id"])
            if not exercise:
                raise HomeworkServiceError("Exercise not found")
            if not task_data.get("paragraph_id"):
                task_data["paragraph_id"] = exercise.paragraph_id

        return await self.repo.add_task(
            homework_id=homework_id,
            data=task_data,
            school_id=school_id
        )

    async def get_task(
        self,
        task_id: int,
        school_id: int,
        load_questions: bool = True
    ) -> Optional[HomeworkTask]:
        """Get task by ID."""
        return await self.repo.get_task_by_id(
            task_id=task_id,
            school_id=school_id,
            load_questions=load_questions
        )

    async def delete_task(self, task_id: int, school_id: int) -> bool:
        """Delete task (soft delete)."""
        task = await self.get_task(task_id, school_id, load_questions=False)
        if not task:
            return False

        homework = await self.get_homework(task.homework_id, school_id, load_tasks=False)
        if homework and homework.status != HomeworkStatus.DRAFT:
            raise HomeworkServiceError("Cannot delete tasks from published homework")

        return await self.repo.delete_task(task_id, school_id)

    # =========================================================================
    # Questions
    # =========================================================================

    async def add_question(
        self,
        task_id: int,
        school_id: int,
        data: QuestionCreate
    ) -> HomeworkTaskQuestion:
        """Add a question to task.

        Args:
            task_id: Parent task ID
            school_id: School ID for RLS (denormalized from task)
            data: Question data
        """
        return await self.repo.add_question(
            task_id=task_id,
            school_id=school_id,
            data=data.model_dump()
        )

    async def add_questions_batch(
        self,
        task_id: int,
        school_id: int,
        questions: List[QuestionCreate]
    ) -> List[HomeworkTaskQuestion]:
        """Add multiple questions to task.

        Args:
            task_id: Parent task ID
            school_id: School ID for RLS (denormalized from task)
            questions: List of question data
        """
        return await self.repo.add_questions_batch(
            task_id=task_id,
            school_id=school_id,
            questions_data=[q.model_dump() for q in questions]
        )

    async def replace_question(
        self,
        question_id: int,
        new_data: QuestionCreate
    ) -> HomeworkTaskQuestion:
        """Replace question with new version (versioning)."""
        return await self.repo.replace_question(
            question_id=question_id,
            new_data=new_data.model_dump()
        )

    # =========================================================================
    # Statistics
    # =========================================================================

    async def get_homework_stats(self, homework_id: int, school_id: int) -> dict:
        """Get homework statistics."""
        return await self.repo.get_homework_stats(
            homework_id=homework_id,
            school_id=school_id
        )

    async def get_homework_stats_batch(self, homework_ids: List[int]) -> Dict[int, dict]:
        """Get statistics for multiple homework in one query."""
        return await self.repo.get_homework_stats_batch(homework_ids)
