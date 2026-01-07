"""
Repository for Student data access.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student import Student
from app.models.user import User


class StudentRepository:
    """Repository for Student CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        student_id: int,
        school_id: int,
        load_user: bool = True,
        load_classes: bool = False,
        load_parents: bool = False
    ) -> Optional[Student]:
        """
        Get student by ID with school isolation.

        Args:
            student_id: Student ID
            school_id: School ID for data isolation
            load_user: Whether to eager load user data
            load_classes: Whether to eager load classes
            load_parents: Whether to eager load parents

        Returns:
            Student or None if not found
        """
        query = select(Student).where(
            Student.id == student_id,
            Student.school_id == school_id,
            Student.is_deleted == False  # noqa: E712
        )

        if load_user:
            query = query.options(selectinload(Student.user))
        if load_classes:
            query = query.options(selectinload(Student.classes))
        if load_parents:
            query = query.options(selectinload(Student.parents))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        school_id: int,
        load_user: bool = True,
        load_classes: bool = False
    ) -> List[Student]:
        """
        Get all students for a specific school.

        Args:
            school_id: School ID for data isolation
            load_user: Whether to eager load user data
            load_classes: Whether to eager load classes

        Returns:
            List of students
        """
        query = select(Student).where(
            Student.school_id == school_id,
            Student.is_deleted == False  # noqa: E712
        ).order_by(Student.created_at.desc())

        if load_user:
            query = query.options(selectinload(Student.user))
        if load_classes:
            query = query.options(selectinload(Student.classes))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_filters(
        self,
        school_id: int,
        grade_level: Optional[int] = None,
        class_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        load_user: bool = True
    ) -> List[Student]:
        """
        Get students with filters.

        Args:
            school_id: School ID for data isolation
            grade_level: Filter by grade level (1-11)
            class_id: Filter by class ID
            is_active: Filter by active status
            load_user: Whether to eager load user data

        Returns:
            List of students matching filters
        """
        filters = [
            Student.school_id == school_id,
            Student.is_deleted == False  # noqa: E712
        ]

        if grade_level is not None:
            filters.append(Student.grade_level == grade_level)

        if is_active is not None:
            filters.append(User.is_active == is_active)

        query = select(Student).join(Student.user).where(and_(*filters))

        # For class_id filter, need to check the association table
        if class_id is not None:
            from app.models.class_student import ClassStudent
            query = query.join(ClassStudent).where(ClassStudent.class_id == class_id)

        query = query.order_by(Student.grade_level, User.last_name, User.first_name)

        if load_user:
            query = query.options(selectinload(Student.user))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_all_paginated(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        grade_level: Optional[int] = None,
        class_id: Optional[int] = None,
        is_active: Optional[bool] = None,
        search: Optional[str] = None,
        load_user: bool = True,
        load_classes: bool = False,
    ) -> Tuple[List[Student], int]:
        """
        Get students with pagination and optional filters.

        Args:
            school_id: School ID for data isolation
            page: Page number (1-indexed)
            page_size: Number of items per page
            grade_level: Filter by grade level (1-11)
            class_id: Filter by class ID
            is_active: Filter by active status
            search: Search by first_name, last_name, or student_code
            load_user: Whether to eager load user data
            load_classes: Whether to eager load classes

        Returns:
            Tuple of (list of students, total count)
        """
        # Build base filters
        filters = [
            Student.school_id == school_id,
            Student.is_deleted == False,  # noqa: E712
        ]

        if grade_level is not None:
            filters.append(Student.grade_level == grade_level)

        # Base query for items - always join User for search
        query = select(Student).join(Student.user)

        # Handle is_active filter
        if is_active is not None:
            filters.append(User.is_active == is_active)

        # Handle search filter
        if search:
            search_filter = f"%{search}%"
            filters.append(
                or_(
                    User.first_name.ilike(search_filter),
                    User.last_name.ilike(search_filter),
                    Student.student_code.ilike(search_filter),
                )
            )

        query = query.where(and_(*filters))

        # Handle class_id filter
        if class_id is not None:
            from app.models.class_student import ClassStudent
            query = query.join(ClassStudent).where(ClassStudent.class_id == class_id)

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering
        query = query.order_by(Student.grade_level, User.last_name, User.first_name)

        # Apply eager loading
        if load_user:
            query = query.options(selectinload(Student.user))
        if load_classes:
            query = query.options(selectinload(Student.classes))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        students = list(result.scalars().all())

        return students, total

    async def get_by_student_code(
        self,
        student_code: str,
        school_id: int
    ) -> Optional[Student]:
        """
        Get student by student code (unique within school).

        Args:
            student_code: Student code
            school_id: School ID for data isolation

        Returns:
            Student or None if not found
        """
        result = await self.db.execute(
            select(Student).where(
                Student.student_code == student_code,
                Student.school_id == school_id,
                Student.is_deleted == False  # noqa: E712
            ).options(selectinload(Student.user))
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: int) -> Optional[Student]:
        """
        Get student by user ID.

        Note: Does not enforce school isolation because we're looking
        up by the specific user_id.

        Args:
            user_id: User ID

        Returns:
            Student or None if not found
        """
        result = await self.db.execute(
            select(Student).where(
                Student.user_id == user_id,
                Student.is_deleted == False  # noqa: E712
            ).options(selectinload(Student.user))
        )
        return result.scalar_one_or_none()

    async def generate_student_code(self, school_id: int) -> str:
        """
        Generate a unique student code for a school.

        Format: STU{school_id}{year}{sequence}
        Example: STU72401 (school 7, year 24, sequence 01)

        Args:
            school_id: School ID

        Returns:
            Generated unique student code
        """
        from datetime import datetime
        from sqlalchemy import func

        year = datetime.now().year % 100  # Last 2 digits of year

        # Get the count of students in this school this year
        # to generate sequence number
        count = await self.count_by_school(school_id)

        # Try to generate unique code
        for attempt in range(100):
            sequence = count + attempt + 1
            code = f"STU{school_id}{year:02d}{sequence:02d}"

            # Check if code exists
            existing = await self.db.execute(
                select(Student).where(Student.student_code == code)
            )
            if not existing.scalar_one_or_none():
                return code

        # Fallback with random suffix
        import secrets
        return f"STU{school_id}{year:02d}{secrets.token_hex(2).upper()}"

    async def create(self, student: Student) -> Student:
        """
        Create a new student.

        Args:
            student: Student instance

        Returns:
            Created student
        """
        self.db.add(student)
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def update(self, student: Student) -> Student:
        """
        Update an existing student.

        Args:
            student: Student instance with updated fields

        Returns:
            Updated student
        """
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def soft_delete(self, student: Student) -> Student:
        """
        Soft delete a student.

        Args:
            student: Student instance

        Returns:
            Deleted student
        """
        from datetime import datetime
        student.is_deleted = True
        student.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(student)
        return student

    async def count_by_school(self, school_id: int) -> int:
        """
        Count students in a school.

        Args:
            school_id: School ID

        Returns:
            Number of students
        """
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(Student.id)).where(
                Student.school_id == school_id,
                Student.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()
