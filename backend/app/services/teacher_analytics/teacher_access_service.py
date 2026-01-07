"""
Teacher Access Service.

Handles teacher lookup and access verification.
"""

import logging
from typing import List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.class_student import ClassStudent
from app.models.class_teacher import ClassTeacher
from app.models.student import Student
from app.models.teacher import Teacher

logger = logging.getLogger(__name__)


class TeacherAccessService:
    """Service for teacher access control and lookup."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_teacher_by_user_id(
        self,
        user_id: int,
        school_id: int
    ) -> Optional[Teacher]:
        """
        Get teacher record by user_id.

        Args:
            user_id: User ID
            school_id: School ID for tenant isolation

        Returns:
            Teacher or None
        """
        result = await self.db.execute(
            select(Teacher)
            .options(selectinload(Teacher.classes))
            .where(
                and_(
                    Teacher.user_id == user_id,
                    Teacher.school_id == school_id,
                    Teacher.is_deleted == False  # noqa: E712
                )
            )
        )
        return result.scalar_one_or_none()

    async def get_teacher_class_ids(self, teacher_id: int) -> List[int]:
        """
        Get list of class IDs assigned to teacher.

        Args:
            teacher_id: Teacher ID

        Returns:
            List of class IDs
        """
        result = await self.db.execute(
            select(ClassTeacher.class_id)
            .where(ClassTeacher.teacher_id == teacher_id)
        )
        return [row[0] for row in result.fetchall()]

    async def verify_teacher_access_to_class(
        self,
        teacher_id: int,
        class_id: int
    ) -> bool:
        """
        Verify teacher has access to a specific class.

        Args:
            teacher_id: Teacher ID
            class_id: Class ID to check

        Returns:
            True if teacher has access, False otherwise
        """
        result = await self.db.execute(
            select(ClassTeacher)
            .where(
                and_(
                    ClassTeacher.teacher_id == teacher_id,
                    ClassTeacher.class_id == class_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_class_students(self, class_id: int) -> List[Student]:
        """
        Get students in a class.

        Args:
            class_id: Class ID

        Returns:
            List of Student objects
        """
        result = await self.db.execute(
            select(Student)
            .join(ClassStudent, ClassStudent.student_id == Student.id)
            .options(selectinload(Student.user))
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    Student.is_deleted == False  # noqa: E712
                )
            )
        )
        return list(result.scalars().all())

    async def get_student_ids_for_classes(self, class_ids: List[int]) -> List[int]:
        """
        Get all student IDs for a list of classes.

        Args:
            class_ids: List of class IDs

        Returns:
            List of unique student IDs
        """
        if not class_ids:
            return []

        result = await self.db.execute(
            select(ClassStudent.student_id.distinct())
            .where(ClassStudent.class_id.in_(class_ids))
        )
        return [row[0] for row in result.fetchall()]
