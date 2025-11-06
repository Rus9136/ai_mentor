"""
Repository for Parent data access.
"""
from typing import Optional, List
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.parent import Parent, parent_students
from app.models.user import User


class ParentRepository:
    """Repository for Parent CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        parent_id: int,
        school_id: int,
        load_user: bool = True,
        load_children: bool = False
    ) -> Optional[Parent]:
        """
        Get parent by ID with school isolation.

        Args:
            parent_id: Parent ID
            school_id: School ID for data isolation
            load_user: Whether to eager load user data
            load_children: Whether to eager load children (students)

        Returns:
            Parent or None if not found
        """
        query = select(Parent).where(
            Parent.id == parent_id,
            Parent.school_id == school_id,
            Parent.is_deleted == False  # noqa: E712
        )

        if load_user:
            query = query.options(selectinload(Parent.user))
        if load_children:
            from app.models.student import Student
            query = query.options(selectinload(Parent.children).selectinload(Student.user))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        school_id: int,
        load_user: bool = True,
        load_children: bool = False
    ) -> List[Parent]:
        """
        Get all parents for a specific school.

        Args:
            school_id: School ID for data isolation
            load_user: Whether to eager load user data
            load_children: Whether to eager load children

        Returns:
            List of parents
        """
        query = select(Parent).where(
            Parent.school_id == school_id,
            Parent.is_deleted == False  # noqa: E712
        ).order_by(Parent.created_at.desc())

        if load_user:
            query = query.options(selectinload(Parent.user))
        if load_children:
            query = query.options(selectinload(Parent.children))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_filters(
        self,
        school_id: int,
        is_active: Optional[bool] = None,
        load_user: bool = True
    ) -> List[Parent]:
        """
        Get parents with filters.

        Args:
            school_id: School ID for data isolation
            is_active: Filter by active status
            load_user: Whether to eager load user data

        Returns:
            List of parents matching filters
        """
        filters = [
            Parent.school_id == school_id,
            Parent.is_deleted == False  # noqa: E712
        ]

        if is_active is not None:
            filters.append(User.is_active == is_active)

        query = select(Parent).join(Parent.user).where(and_(*filters))
        query = query.order_by(User.last_name, User.first_name)

        if load_user:
            query = query.options(selectinload(Parent.user))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def create(self, parent: Parent) -> Parent:
        """
        Create a new parent.

        Args:
            parent: Parent instance

        Returns:
            Created parent
        """
        self.db.add(parent)
        await self.db.commit()
        await self.db.refresh(parent)
        return parent

    async def update(self, parent: Parent) -> Parent:
        """
        Update an existing parent.

        Args:
            parent: Parent instance with updated fields

        Returns:
            Updated parent
        """
        await self.db.commit()
        await self.db.refresh(parent)
        return parent

    async def soft_delete(self, parent: Parent) -> Parent:
        """
        Soft delete a parent.

        Args:
            parent: Parent instance

        Returns:
            Deleted parent
        """
        from datetime import datetime
        parent.is_deleted = True
        parent.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(parent)
        return parent

    async def add_children(
        self,
        parent_id: int,
        student_ids: List[int]
    ) -> Parent:
        """
        Add children (students) to a parent.

        Args:
            parent_id: Parent ID
            student_ids: List of student IDs to add

        Returns:
            Updated parent with children
        """
        from app.models.student import Student

        # Get parent with children eager loaded
        query = select(Parent).where(Parent.id == parent_id).options(selectinload(Parent.children))
        result = await self.db.execute(query)
        parent = result.scalar_one_or_none()

        if not parent:
            raise ValueError(f"Parent {parent_id} not found")

        # Get existing children IDs
        existing_children_ids = {child.id for child in parent.children}

        # Get students and verify they belong to the same school
        for student_id in student_ids:
            # Skip if already exists
            if student_id in existing_children_ids:
                continue

            student = await self.db.get(Student, student_id)
            if not student:
                raise ValueError(f"Student {student_id} not found")
            if student.school_id != parent.school_id:
                raise ValueError(
                    f"Student {student_id} belongs to different school"
                )

            # Add relationship
            parent.children.append(student)

        await self.db.commit()
        await self.db.refresh(parent)
        return parent

    async def remove_children(
        self,
        parent_id: int,
        student_ids: List[int]
    ) -> Parent:
        """
        Remove children (students) from a parent.

        Args:
            parent_id: Parent ID
            student_ids: List of student IDs to remove

        Returns:
            Updated parent
        """
        # Delete rows from parent_students association table
        await self.db.execute(
            delete(parent_students).where(
                and_(
                    parent_students.c.parent_id == parent_id,
                    parent_students.c.student_id.in_(student_ids)
                )
            )
        )
        await self.db.commit()

        # Return refreshed parent
        parent = await self.db.get(Parent, parent_id)
        await self.db.refresh(parent)
        return parent

    async def get_children(
        self,
        parent_id: int,
        school_id: int
    ) -> List["Student"]:
        """
        Get all children (students) for a parent.

        Args:
            parent_id: Parent ID
            school_id: School ID for data isolation

        Returns:
            List of students
        """
        from app.models.student import Student

        parent = await self.get_by_id(parent_id, school_id, load_children=True)
        return parent.children if parent else []

    async def count_by_school(self, school_id: int) -> int:
        """
        Count parents in a school.

        Args:
            school_id: School ID

        Returns:
            Number of parents
        """
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Parent.id)).where(
                Parent.school_id == school_id,
                Parent.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()


# Import Student here to avoid circular import at module level
from app.models.student import Student  # noqa: E402
