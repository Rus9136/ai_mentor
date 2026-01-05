"""
Repository for HomeworkTask operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import (
    HomeworkTask,
    HomeworkTaskQuestion,
)


class HomeworkTaskRepository:
    """Repository for HomeworkTask CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def add_task(
        self,
        homework_id: int,
        data: dict,
        school_id: int
    ) -> HomeworkTask:
        """Add a task to homework."""
        task = HomeworkTask(
            **data,
            homework_id=homework_id,
            school_id=school_id
        )
        self.db.add(task)
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def get_task_by_id(
        self,
        task_id: int,
        school_id: int,
        load_questions: bool = False
    ) -> Optional[HomeworkTask]:
        """Get task by ID."""
        query = select(HomeworkTask).where(
            HomeworkTask.id == task_id,
            HomeworkTask.school_id == school_id,
            HomeworkTask.is_deleted == False
        )

        if load_questions:
            query = query.options(
                selectinload(HomeworkTask.questions.and_(
                    HomeworkTaskQuestion.is_active == True,
                    HomeworkTaskQuestion.is_deleted == False
                ))
            )

        result = await self.db.execute(query)
        task = result.unique().scalar_one_or_none()

        if task and load_questions and task.questions:
            task.questions.sort(key=lambda q: q.sort_order)

        return task

    async def update_task(
        self,
        task_id: int,
        school_id: int,
        data: dict
    ) -> Optional[HomeworkTask]:
        """Update a task."""
        task = await self.get_task_by_id(task_id, school_id)
        if not task:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(task, key, value)

        task.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(task)
        return task

    async def delete_task(self, task_id: int, school_id: int) -> bool:
        """Soft delete a task."""
        task = await self.get_task_by_id(task_id, school_id)
        if task:
            task.is_deleted = True
            task.deleted_at = datetime.utcnow()
            await self.db.flush()
            return True
        return False

    async def reorder_tasks(
        self,
        homework_id: int,
        school_id: int,
        task_ids: List[int]
    ) -> bool:
        """Reorder tasks in homework."""
        for order, task_id in enumerate(task_ids):
            await self.db.execute(
                update(HomeworkTask)
                .where(
                    HomeworkTask.id == task_id,
                    HomeworkTask.homework_id == homework_id,
                    HomeworkTask.school_id == school_id
                )
                .values(sort_order=order)
            )
        await self.db.flush()
        return True
