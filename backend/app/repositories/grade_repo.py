"""
Repository for Grade data access.
"""
import logging
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.grade import Grade, GradeType
from app.models.student import Student
from app.models.user import User
from app.models.subject import Subject

logger = logging.getLogger(__name__)


class GradeRepository:
    """Repository for Grade CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, grade: Grade) -> Grade:
        """Create a new grade record."""
        self.db.add(grade)
        await self.db.flush()
        await self.db.refresh(grade)
        return grade

    async def get_by_id(self, grade_id: int, school_id: int) -> Optional[Grade]:
        """Get a grade by ID with school isolation."""
        result = await self.db.execute(
            select(Grade)
            .where(
                Grade.id == grade_id,
                Grade.school_id == school_id,
                Grade.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def update(self, grade: Grade) -> Grade:
        """Update a grade record."""
        grade.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(grade)
        return grade

    async def soft_delete(self, grade: Grade) -> None:
        """Soft delete a grade."""
        grade.is_deleted = True
        grade.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def get_by_student_subject(
        self,
        student_id: int,
        subject_id: int,
        school_id: int,
        quarter: Optional[int] = None,
        academic_year: Optional[str] = None,
        grade_type: Optional[GradeType] = None,
    ) -> List[Grade]:
        """Get grades for a student in a subject."""
        filters = [
            Grade.student_id == student_id,
            Grade.subject_id == subject_id,
            Grade.school_id == school_id,
            Grade.is_deleted == False,
        ]
        if quarter is not None:
            filters.append(Grade.quarter == quarter)
        if academic_year is not None:
            filters.append(Grade.academic_year == academic_year)
        if grade_type is not None:
            filters.append(Grade.grade_type == grade_type)

        result = await self.db.execute(
            select(Grade)
            .where(and_(*filters))
            .order_by(Grade.grade_date.desc(), Grade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_class_subject(
        self,
        class_id: int,
        subject_id: int,
        school_id: int,
        quarter: Optional[int] = None,
        academic_year: Optional[str] = None,
        grade_type: Optional[GradeType] = None,
    ) -> List[Grade]:
        """Get all grades for a class in a subject (class journal view)."""
        filters = [
            Grade.class_id == class_id,
            Grade.subject_id == subject_id,
            Grade.school_id == school_id,
            Grade.is_deleted == False,
        ]
        if quarter is not None:
            filters.append(Grade.quarter == quarter)
        if academic_year is not None:
            filters.append(Grade.academic_year == academic_year)
        if grade_type is not None:
            filters.append(Grade.grade_type == grade_type)

        result = await self.db.execute(
            select(Grade)
            .where(and_(*filters))
            .order_by(Grade.grade_date.desc(), Grade.student_id, Grade.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_student_quarter(
        self,
        student_id: int,
        school_id: int,
        quarter: int,
        academic_year: str,
    ) -> List[Grade]:
        """Get all grades for a student in a quarter."""
        result = await self.db.execute(
            select(Grade)
            .where(
                Grade.student_id == student_id,
                Grade.school_id == school_id,
                Grade.quarter == quarter,
                Grade.academic_year == academic_year,
                Grade.is_deleted == False,
            )
            .order_by(Grade.subject_id, Grade.grade_date.desc())
        )
        return list(result.scalars().all())

    async def get_student_grades_paginated(
        self,
        student_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        subject_id: Optional[int] = None,
        quarter: Optional[int] = None,
        academic_year: Optional[str] = None,
    ) -> Tuple[List[Grade], int]:
        """Get paginated grades for a student."""
        filters = [
            Grade.student_id == student_id,
            Grade.school_id == school_id,
            Grade.is_deleted == False,
        ]
        if subject_id is not None:
            filters.append(Grade.subject_id == subject_id)
        if quarter is not None:
            filters.append(Grade.quarter == quarter)
        if academic_year is not None:
            filters.append(Grade.academic_year == academic_year)

        where_clause = and_(*filters)

        # Count
        count_query = select(func.count()).select_from(Grade).where(where_clause)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Items
        offset = (page - 1) * page_size
        items_query = (
            select(Grade)
            .where(where_clause)
            .order_by(Grade.grade_date.desc(), Grade.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        result = await self.db.execute(items_query)
        items = list(result.scalars().all())

        return items, total
