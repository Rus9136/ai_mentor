"""
Repository for Teacher data access.
"""
from typing import Optional, List
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.teacher import Teacher
from app.models.user import User
from app.models.subject import Subject


class TeacherRepository:
    """Repository for Teacher CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        teacher_id: int,
        school_id: int,
        load_user: bool = True,
        load_classes: bool = False,
        load_subject: bool = True
    ) -> Optional[Teacher]:
        """
        Get teacher by ID with school isolation.

        Args:
            teacher_id: Teacher ID
            school_id: School ID for data isolation
            load_user: Whether to eager load user data
            load_classes: Whether to eager load classes
            load_subject: Whether to eager load subject (default True)

        Returns:
            Teacher or None if not found
        """
        query = select(Teacher).where(
            Teacher.id == teacher_id,
            Teacher.school_id == school_id,
            Teacher.is_deleted == False  # noqa: E712
        )

        if load_user:
            query = query.options(selectinload(Teacher.user))
        if load_classes:
            query = query.options(selectinload(Teacher.classes))
        if load_subject:
            query = query.options(selectinload(Teacher.subject_rel))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        school_id: int,
        load_user: bool = True,
        load_classes: bool = False,
        load_subject: bool = True
    ) -> List[Teacher]:
        """
        Get all teachers for a specific school.

        Args:
            school_id: School ID for data isolation
            load_user: Whether to eager load user data
            load_classes: Whether to eager load classes
            load_subject: Whether to eager load subject (default True)

        Returns:
            List of teachers
        """
        query = select(Teacher).where(
            Teacher.school_id == school_id,
            Teacher.is_deleted == False  # noqa: E712
        ).order_by(Teacher.created_at.desc())

        if load_user:
            query = query.options(selectinload(Teacher.user))
        if load_classes:
            query = query.options(selectinload(Teacher.classes))
        if load_subject:
            query = query.options(selectinload(Teacher.subject_rel))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_filters(
        self,
        school_id: int,
        subject_id: Optional[int] = None,
        class_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        load_user: bool = True,
        load_subject: bool = True
    ) -> List[Teacher]:
        """
        Get teachers with filters.

        Args:
            school_id: School ID for data isolation
            subject_id: Filter by subject ID
            class_id: Filter by class ID
            is_active: Filter by active status
            load_user: Whether to eager load user data
            load_subject: Whether to eager load subject (default True)

        Returns:
            List of teachers matching filters
        """
        filters = [
            Teacher.school_id == school_id,
            Teacher.is_deleted == False  # noqa: E712
        ]

        if subject_id is not None:
            filters.append(Teacher.subject_id == subject_id)

        if is_active is not None:
            filters.append(User.is_active == is_active)

        query = select(Teacher).join(Teacher.user).where(and_(*filters))

        # For class_id filter, need to check the association table
        if class_id is not None:
            from app.models.class_teacher import ClassTeacher
            query = query.join(ClassTeacher).where(ClassTeacher.class_id == class_id)

        query = query.order_by(User.last_name, User.first_name)

        if load_user:
            query = query.options(selectinload(Teacher.user))
        if load_subject:
            query = query.options(selectinload(Teacher.subject_rel))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_teacher_code(
        self,
        teacher_code: str,
        school_id: int
    ) -> Optional[Teacher]:
        """
        Get teacher by teacher code (unique within school).

        Args:
            teacher_code: Teacher code
            school_id: School ID for data isolation

        Returns:
            Teacher or None if not found
        """
        result = await self.db.execute(
            select(Teacher).where(
                Teacher.teacher_code == teacher_code,
                Teacher.school_id == school_id,
                Teacher.is_deleted == False  # noqa: E712
            ).options(selectinload(Teacher.user))
        )
        return result.scalar_one_or_none()

    async def create(self, teacher: Teacher) -> Teacher:
        """
        Create a new teacher.

        Args:
            teacher: Teacher instance

        Returns:
            Created teacher
        """
        self.db.add(teacher)
        await self.db.commit()
        await self.db.refresh(teacher)
        return teacher

    async def update(self, teacher: Teacher) -> Teacher:
        """
        Update an existing teacher.

        Args:
            teacher: Teacher instance with updated fields

        Returns:
            Updated teacher
        """
        await self.db.commit()
        await self.db.refresh(teacher)
        return teacher

    async def soft_delete(self, teacher: Teacher) -> Teacher:
        """
        Soft delete a teacher.

        Args:
            teacher: Teacher instance

        Returns:
            Deleted teacher
        """
        from datetime import datetime
        teacher.is_deleted = True
        teacher.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(teacher)
        return teacher

    async def count_by_school(self, school_id: int) -> int:
        """
        Count teachers in a school.

        Args:
            school_id: School ID

        Returns:
            Number of teachers
        """
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Teacher.id)).where(
                Teacher.school_id == school_id,
                Teacher.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()
