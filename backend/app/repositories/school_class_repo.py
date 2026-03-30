"""
Repository for SchoolClass data access.
"""
from typing import Optional, List, Tuple, Any
from sqlalchemy import select, and_, delete, func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

_NOT_SET: Any = object()

from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent
from app.models.class_teacher import ClassTeacher
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.subject import Subject


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
        """Get school class by ID with school isolation."""
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
                selectinload(SchoolClass.teachers).selectinload(Teacher.user),
                selectinload(SchoolClass.class_teachers)
                .joinedload(ClassTeacher.teacher)
                .selectinload(Teacher.user),
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        school_id: int,
        load_students: bool = False,
        load_teachers: bool = False
    ) -> List[SchoolClass]:
        """Get all classes for a specific school."""
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
        """Get classes with filters."""
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

    async def get_all_paginated(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        grade_level: Optional[int] = None,
        academic_year: Optional[str] = None,
        load_students: bool = False,
        load_teachers: bool = False,
    ) -> Tuple[List[SchoolClass], int]:
        """Get classes with pagination and optional filters."""
        # Build base filters
        filters = [
            SchoolClass.school_id == school_id,
            SchoolClass.is_deleted == False,  # noqa: E712
        ]

        if grade_level is not None:
            filters.append(SchoolClass.grade_level == grade_level)

        if academic_year is not None:
            filters.append(SchoolClass.academic_year == academic_year)

        # Base query
        query = select(SchoolClass).where(and_(*filters))

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering
        query = query.order_by(SchoolClass.grade_level, SchoolClass.name)

        # Apply eager loading
        if load_students:
            query = query.options(
                selectinload(SchoolClass.students).selectinload(Student.user)
            )
        if load_teachers:
            query = query.options(
                selectinload(SchoolClass.teachers).selectinload(Teacher.user)
            )

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        classes = list(result.scalars().all())

        return classes, total

    async def get_by_code(
        self,
        code: str,
        school_id: int
    ) -> Optional[SchoolClass]:
        """Get class by code (unique within school)."""
        result = await self.db.execute(
            select(SchoolClass).where(
                SchoolClass.code == code,
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def create(self, school_class: SchoolClass) -> SchoolClass:
        """Create a new school class."""
        self.db.add(school_class)
        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def update(self, school_class: SchoolClass) -> SchoolClass:
        """Update an existing school class."""
        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def soft_delete(self, school_class: SchoolClass) -> SchoolClass:
        """Soft delete a school class."""
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
        """Add students to a class."""
        school_class = await self.get_by_id(class_id, school_id)
        if not school_class:
            raise ValueError(f"Class {class_id} not found")

        # Get existing student IDs via direct query (avoid lazy loading in async)
        result = await self.db.execute(
            select(ClassStudent.student_id).where(ClassStudent.class_id == class_id)
        )
        existing_ids = {row[0] for row in result.all()}

        # Verify all students exist and belong to the same school
        for student_id in student_ids:
            if student_id in existing_ids:
                continue  # Already in class

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

            # Use association object directly (school_class.students is viewonly=True)
            assoc = ClassStudent(class_id=class_id, student_id=student_id)
            self.db.add(assoc)

        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def remove_students(
        self,
        class_id: int,
        student_ids: List[int],
        school_id: Optional[int] = None
    ) -> SchoolClass:
        """Remove students from a class."""
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
        """Get all students in a class."""
        school_class = await self.get_by_id(class_id, school_id, load_students=True)
        return school_class.students if school_class else []

    # Teacher management methods

    async def add_teachers(
        self,
        class_id: int,
        assignments: list,
        school_id: int
    ) -> SchoolClass:
        """
        Add teachers to a class with subject assignments.

        Args:
            class_id: Class ID
            assignments: List of dicts/objects with teacher_id, subject_id, is_homeroom
            school_id: School ID for validation
        """
        school_class = await self.get_by_id(class_id, school_id)
        if not school_class:
            raise ValueError(f"Class {class_id} not found")

        # Get existing assignments to avoid duplicates
        result = await self.db.execute(
            select(ClassTeacher.teacher_id, ClassTeacher.subject_id)
            .where(ClassTeacher.class_id == class_id)
        )
        existing = {(row[0], row[1]) for row in result.all()}

        for assignment in assignments:
            teacher_id = assignment.teacher_id if hasattr(assignment, 'teacher_id') else assignment['teacher_id']
            subject_id = assignment.subject_id if hasattr(assignment, 'subject_id') else assignment.get('subject_id')
            is_homeroom = assignment.is_homeroom if hasattr(assignment, 'is_homeroom') else assignment.get('is_homeroom', False)

            # Skip if already assigned with same subject
            if (teacher_id, subject_id) in existing:
                continue

            # Verify teacher exists and belongs to same school
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

            # Verify subject exists if provided
            if subject_id is not None:
                result = await self.db.execute(
                    select(Subject.id).where(Subject.id == subject_id)
                )
                if not result.scalar_one_or_none():
                    raise ValueError(f"Subject {subject_id} not found")

            # Handle homeroom: unset existing homeroom if new one is being set
            if is_homeroom:
                await self.db.execute(
                    update(ClassTeacher)
                    .where(ClassTeacher.class_id == class_id, ClassTeacher.is_homeroom == True)  # noqa: E712
                    .values(is_homeroom=False)
                )

            class_teacher = ClassTeacher(
                class_id=class_id,
                teacher_id=teacher_id,
                subject_id=subject_id,
                is_homeroom=is_homeroom,
            )
            self.db.add(class_teacher)

        await self.db.commit()
        await self.db.refresh(school_class)
        return school_class

    async def remove_teachers(
        self,
        class_id: int,
        teacher_ids: List[int],
        school_id: Optional[int] = None,
        subject_id: Any = _NOT_SET,
    ) -> SchoolClass:
        """
        Remove teachers from a class.

        If subject_id is provided, only remove the specific subject assignment.
        If subject_id is "NOT_SET" (default), remove all assignments for the teacher.
        """
        conditions = [
            ClassTeacher.class_id == class_id,
            ClassTeacher.teacher_id.in_(teacher_ids)
        ]
        if subject_id is not _NOT_SET:
            if subject_id is None:
                conditions.append(ClassTeacher.subject_id.is_(None))
            else:
                conditions.append(ClassTeacher.subject_id == subject_id)

        await self.db.execute(
            delete(ClassTeacher).where(and_(*conditions))
        )
        await self.db.commit()
        # Expire cached objects so reload sees fresh data
        self.db.expire_all()

        # Return refreshed class
        if school_id is not None:
            school_class = await self.get_by_id(class_id, school_id)
            if not school_class:
                raise ValueError(f"Class {class_id} not found")
        else:
            school_class = await self.db.get(SchoolClass, class_id)
            await self.db.refresh(school_class)
        return school_class

    async def set_homeroom_teacher(
        self,
        class_id: int,
        teacher_id: int,
        school_id: int,
    ) -> SchoolClass:
        """
        Set a teacher as homeroom (классный руководитель) for a class.
        Unsets any existing homeroom teacher for this class.
        """
        # Verify teacher is assigned to this class
        result = await self.db.execute(
            select(ClassTeacher).where(
                ClassTeacher.class_id == class_id,
                ClassTeacher.teacher_id == teacher_id,
            )
        )
        ct = result.scalars().first()
        if not ct:
            raise ValueError(f"Teacher {teacher_id} is not assigned to class {class_id}")

        # Unset all homeroom flags for this class
        await self.db.execute(
            update(ClassTeacher)
            .where(ClassTeacher.class_id == class_id, ClassTeacher.is_homeroom == True)  # noqa: E712
            .values(is_homeroom=False)
        )

        # Set the new homeroom teacher (on their first assignment row)
        await self.db.execute(
            update(ClassTeacher)
            .where(ClassTeacher.id == ct.id)
            .values(is_homeroom=True)
        )

        await self.db.commit()

        school_class = await self.get_by_id(class_id, school_id, load_teachers=True)
        return school_class

    async def unset_homeroom_teacher(
        self,
        class_id: int,
        school_id: int,
    ) -> SchoolClass:
        """Remove homeroom designation from all teachers in a class."""
        await self.db.execute(
            update(ClassTeacher)
            .where(ClassTeacher.class_id == class_id, ClassTeacher.is_homeroom == True)  # noqa: E712
            .values(is_homeroom=False)
        )
        await self.db.commit()

        school_class = await self.get_by_id(class_id, school_id, load_teachers=True)
        return school_class

    async def get_class_teacher_assignments(
        self,
        class_id: int,
    ) -> List[ClassTeacher]:
        """Get all teacher assignments for a class with eager-loaded relations."""
        result = await self.db.execute(
            select(ClassTeacher)
            .where(ClassTeacher.class_id == class_id)
            .options(
                joinedload(ClassTeacher.teacher).selectinload(Teacher.user),
            )
        )
        return list(result.scalars().unique().all())

    async def get_teachers(
        self,
        class_id: int,
        school_id: int
    ) -> List[Teacher]:
        """Get all teachers for a class."""
        school_class = await self.get_by_id(class_id, school_id, load_teachers=True)
        return school_class.teachers if school_class else []

    async def count_by_school(self, school_id: int) -> int:
        """Count classes in a school."""
        from sqlalchemy import func
        result = await self.db.execute(
            select(func.count(SchoolClass.id)).where(
                SchoolClass.school_id == school_id,
                SchoolClass.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one()

    async def remove_student_from_all_classes(
        self,
        student_id: int,
        school_id: Optional[int] = None
    ) -> int:
        """Remove student from all classes."""
        if school_id is not None:
            subquery = (
                select(SchoolClass.id)
                .where(SchoolClass.school_id == school_id)
            )
            delete_stmt = delete(ClassStudent).where(
                and_(
                    ClassStudent.student_id == student_id,
                    ClassStudent.class_id.in_(subquery)
                )
            )
        else:
            delete_stmt = delete(ClassStudent).where(
                ClassStudent.student_id == student_id
            )

        result = await self.db.execute(delete_stmt)
        await self.db.commit()
        return result.rowcount
