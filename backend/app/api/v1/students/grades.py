"""
Student API endpoints for viewing grades (read-only).

Students can only view their own grades.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import require_student, get_current_user_school_id, get_student_from_user
from app.services.grade_service import GradeService
from app.schemas.grade import GradeResponse

router = APIRouter()


@router.get(
    "/grades",
    response_model=List[GradeResponse],
    summary="Get my grades",
)
async def get_my_grades(
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter (1-4)"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current student's grades. Optionally filter by subject, quarter, year."""
    student = await get_student_from_user(current_user, db)

    service = GradeService(db)
    if subject_id:
        return await service.get_student_subject_grades(
            student_id=student.id,
            subject_id=subject_id,
            school_id=school_id,
            quarter=quarter,
            academic_year=academic_year,
        )

    grades, _ = await service.get_student_grades(
        student_id=student.id,
        school_id=school_id,
        subject_id=subject_id,
        quarter=quarter,
        academic_year=academic_year,
    )
    return grades


@router.get(
    "/grades/subject/{subject_id}",
    response_model=List[GradeResponse],
    summary="Get my grades for a subject",
)
async def get_my_grades_by_subject(
    subject_id: int,
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter (1-4)"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current student's grades for a specific subject."""
    student = await get_student_from_user(current_user, db)

    service = GradeService(db)
    return await service.get_student_subject_grades(
        student_id=student.id,
        subject_id=subject_id,
        school_id=school_id,
        quarter=quarter,
        academic_year=academic_year,
    )
