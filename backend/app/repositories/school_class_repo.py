"""
Repository for SchoolClass data access.
"""
from typing import Optional, List
from sqlalchemy import select, and_, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent
from app.models.class_teacher import ClassTeacher
from app.models.student import Student
from app.models.teacher import Teacher


class SchoolClassRepository:
    """Repository for SchoolClass CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        class_id: int,
        school_id: int,
        load_students: bool = False,
        load_teachers: bool = False
    ) -> Optional[SchoolClass]:
        """
        Get school class by ID with school isolation.

        Args:
            class_id: Class ID
            school_id: School ID for data isolation
            load_students: Whether to eager load students
            load_teachers: Whether to eager load teachers

        Returns:
            SchoolClass or None if not found
        """
        query = select(SchoolClass).where(
            SchoolClass.id == class_id,
            SchoolClass.school_id == school_id,
            SchoolClass.is_deleted == False  # noqa: E712
        )

        if load_students:
            query = query.options(
                selectinload(SchoolClass.students).selectinload(Student.user)
            )
        if load_teachers:
            query = query.options(
                selectinload(SchoolClass.teachers).selectinload(Teacher.user)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        school_id: int,
        load_students: bool = False,
        load_teachers: bool = False
    ) -> List[SchoolClass]:
        """
        Get all classes for a specific school.

        Args:
            school_id: School ID for data isolation
            load_students: Whether to eager load students
            load_teachers: Whether to eager load teachers

        Returns:
            List of school classes
        """
        query = select(SchoolClass).where(
            SchoolClass.school_id == school_id,
            SchoolClass.is_deleted == False  # noqa: E712
        ).order_by(SchoolClass.grade_level, SchoolClass.name)

        if load_students:
            query = query.options(selectinload(SchoolClass.students))
        if load_teachers:
            query = query.options(selectinload(SchoolClass.teachers))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_filters(
        self,
        school_id: int,
        grade_level: Optional[int] = None,
        academic_year: Optional[str] = None,
        load_students: bool = False,
        load_teachers: bool = False
    ) -> List[SchoolClass]:
        """
        Get classes with filters.

        Args:
            school_id: School ID for data isolation
            grade_level: Filter by grade level (1-11)
            academic_year: Filter by academic year
            load_students: Whether to eager load students
            load_teachers: Whether to eager load teachers

        Returns:
            List of school classes matching filters
        """
        filters = [
            SchoolClass.school_id == school_id,
            SchoolClass.is_deleted == False  # noqa: E712
        ]

        if grade_level is not None:
            filters.append(SchoolClass.grade_level == grade_level)

        if academic_year is not None:
            filters.append(SchoolClass.academic_year == academic_year)

        query = select(SchoolClass).where(and_(*filters))
        query = query.order_by(SchoolClass.grade_level, SchoolClass.name)

        if load_students:
            query = query.options(selectinload(SchoolClass.students))
        if load_teachers:
            query = query.options(selectinload(SchoolClass.teachers))

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_code(
        self,
        code: str,
        school_id: int
    ) -> Optional[SchoolClass]:
        """
        Get class by code (unique within school).

        Args:
            code: Class code
            school_id: School ID for data isolation

        Returns:
            SchoolClass or None if not found
        """
        result = await self.db.execute(
            select(SchoolClass).where(
                SchoolClass.code == code,
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def create(self, school_class: SchoolClass) -> SchoolClass:
        """
        Create a new school class.

        Args:
            school_class: SchoolClass instance

        Returns:
            Created school class
        """
        self.db.add(school_class)
        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def update(self, school_class: SchoolClass) -> SchoolClass:
        """
        Update an existing school class.

        Args:
            school_class: SchoolClass instance with updated fields

        Returns:
            Updated school class
        """
        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def soft_delete(self, school_class: SchoolClass) -> SchoolClass:
        """
        Soft delete a school class.

        Args:
            school_class: SchoolClass instance

        Returns:
            Deleted school class
        """
        from datetime import datetime
        school_class.is_deleted = True
        school_class.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    # Student management methods

    async def add_students(
        self,
        class_id: int,
        student_ids: List[int],
        school_id: int
    ) -> SchoolClass:
        """
        Add students to a class.

        Args:
            class_id: Class ID
            student_ids: List of student IDs to add
            school_id: School ID for validation

        Returns:
            Updated school class with students

        Raises:
            ValueError: If class or students not found, or belong to different schools
        """
        # Get class with students loaded to avoid lazy loading
        school_class = await self.get_by_id(class_id, school_id, load_students=True)
        if not school_class:
            raise ValueError(f"Class {class_id} not found")

        # Verify all students exist and belong to the same school
        for student_id in student_ids:
            # Query with school_id and is_deleted filter
            result = await self.db.execute(
                select(Student).where(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    Student.is_deleted == False  # noqa: E712
                )
            )
            student = result.scalar_one_or_none()

            if not student:
                raise ValueError(
                    f"Student {student_id} not found or belongs to different school"
                )

            # Add relationship if not exists
            if student not in school_class.students:
                school_class.students.append(student)

        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def remove_students(
        self,
        class_id: int,
        student_ids: List[int],
        school_id: Optional[int] = None
    ) -> SchoolClass:
        """
        Remove students from a class.

        Args:
            class_id: Class ID
            student_ids: List of student IDs to remove
            school_id: School ID for data isolation (optional for backward compatibility)

        Returns:
            Updated school class
        """
        # Delete rows from class_students association table
        await self.db.execute(
            delete(ClassStudent).where(
                and_(
                    ClassStudent.class_id == class_id,
                    ClassStudent.student_id.in_(student_ids)
                )
            )
        )
        await self.db.commit()

        # Return refreshed class with school_id check if provided
        if school_id is not None:
            school_class = await self.get_by_id(class_id, school_id)
            if not school_class:
                raise ValueError(f"Class {class_id} not found")
        else:
            # Fallback for backward compatibility
            school_class = await self.db.get(SchoolClass, class_id)
            await self.db.refresh(school_class)
        return school_class

    async def get_students(
        self,
        class_id: int,
        school_id: int
    ) -> List[Student]:
        """
        Get all students in a class.

        Args:
            class_id: Class ID
            school_id: School ID for data isolation

        Returns:
            List of students
        """
        school_class = await self.get_by_id(class_id, school_id, load_students=True)
        return school_class.students if school_class else []

    # Teacher management methods

    async def add_teachers(
        self,
        class_id: int,
        teacher_ids: List[int],
        school_id: int
    ) -> SchoolClass:
        """
        Add teachers to a class.

        Args:
            class_id: Class ID
            teacher_ids: List of teacher IDs to add
            school_id: School ID for validation

        Returns:
            Updated school class with teachers

        Raises:
            ValueError: If class or teachers not found, or belong to different schools
        """
        # Get class with teachers loaded to avoid lazy loading
        school_class = await self.get_by_id(class_id, school_id, load_teachers=True)
        if not school_class:
            raise ValueError(f"Class {class_id} not found")

        # Verify all teachers exist and belong to the same school
        for teacher_id in teacher_ids:
            # Query with school_id and is_deleted filter
            result = await self.db.execute(
                select(Teacher).where(
                    Teacher.id == teacher_id,
                    Teacher.school_id == school_id,
                    Teacher.is_deleted == False  # noqa: E712
                )
            )
            teacher = result.scalar_one_or_none()

            if not teacher:
                raise ValueError(
                    f"Teacher {teacher_id} not found or belongs to different school"
                )

            # Add relationship if not exists
            if teacher not in school_class.teachers:
                school_class.teachers.append(teacher)

        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def remove_teachers(
        self,
        class_id: int,
        teacher_ids: List[int],
        school_id: Optional[int] = None
    ) -> SchoolClass:
        """
        Remove teachers from a class.

        Args:
            class_id: Class ID
            teacher_ids: List of teacher IDs to remove
            school_id: School ID for data isolation (optional for backward compatibility)

        Returns:
            Updated school class
        """
        # Delete rows from class_teachers association table
        await self.db.execute(
            delete(ClassTeacher).where(
                and_(
                    ClassTeacher.class_id == class_id,
                    ClassTeacher.teacher_id.in_(teacher_ids)
                )
            )
        )
        await self.db.commit()

        # Return refreshed class with school_id check if provided
        if school_id is not None:
            school_class = await self.get_by_id(class_id, school_id)
            if not school_class:
                raise ValueError(f"Class {class_id} not found")
        else:
            # Fallback for backward compatibility
            school_class = await self.db.get(SchoolClass, class_id)
            await self.db.refresh(school_class)
        return school_class

    async def get_teachers(
        self,
        class_id: int,
        school_id: int
    ) -> List[Teacher]:
        """
        Get all teachers for a class.

        Args:
            class_id: Class ID
            school_id: School ID for data isolation

        Returns:
            List of teachers
        """
        school_class = await self.get_by_id(class_id, school_id, load_teachers=True)
        return school_class.teachers if school_class else []

    async def count_by_school(self, school_id: int) -> int:
        """
        Count classes in a school.

        Args:
            school_id: School ID

        Returns:
            Number of classes
        """
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(SchoolClass.id)).where(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()
