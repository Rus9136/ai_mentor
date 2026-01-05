"""
Repository for Homework CRUD operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStatus,
)


class HomeworkCrudRepository:
    """Repository for Homework entity CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        data: dict,
        school_id: int,
        teacher_id: int
    ) -> Homework:
        """Create a new homework assignment."""
        homework = Homework(
            **data,
            school_id=school_id,
            teacher_id=teacher_id,
            status=HomeworkStatus.DRAFT
        )
        self.db.add(homework)
        await self.db.flush()
        await self.db.refresh(homework)
        return homework

    async def get_by_id(
        self,
        homework_id: int,
        school_id: int,
        load_tasks: bool = False,
        load_questions: bool = False
    ) -> Optional[Homework]:
        """Get homework by ID with optional eager loading."""
        query = select(Homework).where(
            Homework.id == homework_id,
            Homework.school_id == school_id,
            Homework.is_deleted == False
        )

        if load_tasks:
            if load_questions:
                query = query.options(
                    selectinload(Homework.tasks)
                    .selectinload(HomeworkTask.questions.and_(
                        HomeworkTaskQuestion.is_active == True,
                        HomeworkTaskQuestion.is_deleted == False
                    ))
                )
            else:
                query = query.options(selectinload(Homework.tasks))

        result = await self.db.execute(query)
        homework = result.unique().scalar_one_or_none()

        if homework and load_tasks and homework.tasks:
            homework.tasks.sort(key=lambda t: t.sort_order)
            if load_questions:
                for task in homework.tasks:
                    if task.questions:
                        task.questions.sort(key=lambda q: q.sort_order)

        return homework

    async def list_by_teacher(
        self,
        teacher_id: int,
        school_id: int,
        class_id: Optional[int] = None,
        status: Optional[HomeworkStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Homework]:
        """List homework assignments for a teacher."""
        query = (
            select(Homework)
            .options(selectinload(Homework.tasks))
            .where(
                Homework.teacher_id == teacher_id,
                Homework.school_id == school_id,
                Homework.is_deleted == False
            )
        )

        if class_id:
            query = query.where(Homework.class_id == class_id)

        if status:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.due_date.desc()).offset(offset).limit(limit)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def list_by_class(
        self,
        class_id: int,
        school_id: int,
        status: Optional[HomeworkStatus] = None,
        include_stats: bool = False
    ) -> List[Homework]:
        """List homework for a class."""
        query = (
            select(Homework)
            .where(
                Homework.class_id == class_id,
                Homework.school_id == school_id,
                Homework.is_deleted == False
            )
        )

        if status:
            query = query.where(Homework.status == status)

        query = query.order_by(Homework.due_date.desc())

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update(
        self,
        homework_id: int,
        school_id: int,
        data: dict
    ) -> Optional[Homework]:
        """Update homework assignment."""
        homework = await self.get_by_id(homework_id, school_id)
        if not homework:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(homework, key, value)

        homework.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(homework)
        return homework

    async def update_status(
        self,
        homework_id: int,
        school_id: int,
        status: HomeworkStatus
    ) -> Optional[Homework]:
        """Update homework status."""
        homework = await self.get_by_id(homework_id, school_id)
        if homework:
            homework.status = status
            homework.updated_at = datetime.utcnow()
            await self.db.flush()
        return homework

    async def soft_delete(self, homework_id: int, school_id: int) -> bool:
        """Soft delete homework."""
        homework = await self.get_by_id(homework_id, school_id)
        if homework:
            homework.is_deleted = True
            homework.deleted_at = datetime.utcnow()
            await self.db.flush()
            return True
        return False
