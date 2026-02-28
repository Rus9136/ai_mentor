"""
Grade Service.

Handles business logic for school gradebook:
- Create/update/delete grades
- Validation (student belongs to school, subject exists)
- Journal views (by student, by class)
"""
import logging
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.grade import Grade, GradeType
from app.models.student import Student
from app.models.subject import Subject
from app.models.teacher import Teacher
from app.repositories.grade_repo import GradeRepository
from app.schemas.grade import GradeCreate, GradeUpdate

logger = logging.getLogger(__name__)


class GradeService:
    """Service for grade operations."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = GradeRepository(db)

    async def record_grade(
        self,
        data: GradeCreate,
        school_id: int,
        user_id: int,
        teacher_id: Optional[int] = None,
    ) -> Grade:
        """
        Create a new grade.

        Validates that the student and subject belong to the school.
        """
        # Validate student belongs to school
        result = await self.db.execute(
            select(Student).where(
                Student.id == data.student_id,
                Student.school_id == school_id,
                Student.is_deleted == False,
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Student {data.student_id} not found in this school",
            )

        # Validate subject exists
        result = await self.db.execute(
            select(Subject).where(
                Subject.id == data.subject_id,
                Subject.is_active == True,
            )
        )
        subject = result.scalar_one_or_none()
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Subject {data.subject_id} not found",
            )

        grade = Grade(
            student_id=data.student_id,
            school_id=school_id,
            subject_id=data.subject_id,
            class_id=data.class_id,
            teacher_id=teacher_id,
            created_by=user_id,
            grade_value=data.grade_value,
            grade_type=data.grade_type,
            grade_date=data.grade_date,
            quarter=data.quarter,
            academic_year=data.academic_year,
            comment=data.comment,
        )

        grade = await self.repo.create(grade)
        await self.db.commit()

        logger.info(
            f"Grade recorded: id={grade.id}, student={data.student_id}, "
            f"subject={data.subject_id}, value={data.grade_value}, "
            f"type={data.grade_type}, by_user={user_id}"
        )

        return grade

    async def update_grade(
        self,
        grade_id: int,
        data: GradeUpdate,
        school_id: int,
    ) -> Grade:
        """Update an existing grade."""
        grade = await self.repo.get_by_id(grade_id, school_id)
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grade {grade_id} not found",
            )

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(grade, field, value)

        grade = await self.repo.update(grade)
        await self.db.commit()

        logger.info(f"Grade updated: id={grade_id}, fields={list(update_data.keys())}")
        return grade

    async def delete_grade(
        self,
        grade_id: int,
        school_id: int,
    ) -> None:
        """Soft delete a grade."""
        grade = await self.repo.get_by_id(grade_id, school_id)
        if not grade:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Grade {grade_id} not found",
            )

        await self.repo.soft_delete(grade)
        await self.db.commit()

        logger.info(f"Grade deleted: id={grade_id}")

    async def get_class_journal(
        self,
        class_id: int,
        subject_id: int,
        school_id: int,
        quarter: Optional[int] = None,
        academic_year: Optional[str] = None,
        grade_type: Optional[GradeType] = None,
    ) -> List[Grade]:
        """Get grades for a class journal view."""
        return await self.repo.get_by_class_subject(
            class_id=class_id,
            subject_id=subject_id,
            school_id=school_id,
            quarter=quarter,
            academic_year=academic_year,
            grade_type=grade_type,
        )

    async def get_student_grades(
        self,
        student_id: int,
        school_id: int,
        subject_id: Optional[int] = None,
        quarter: Optional[int] = None,
        academic_year: Optional[str] = None,
    ) -> Tuple[List[Grade], int]:
        """Get paginated grades for a student."""
        return await self.repo.get_student_grades_paginated(
            student_id=student_id,
            school_id=school_id,
            subject_id=subject_id,
            quarter=quarter,
            academic_year=academic_year,
        )

    async def get_student_subject_grades(
        self,
        student_id: int,
        subject_id: int,
        school_id: int,
        quarter: Optional[int] = None,
        academic_year: Optional[str] = None,
    ) -> List[Grade]:
        """Get grades for a student in a specific subject."""
        return await self.repo.get_by_student_subject(
            student_id=student_id,
            subject_id=subject_id,
            school_id=school_id,
            quarter=quarter,
            academic_year=academic_year,
        )
