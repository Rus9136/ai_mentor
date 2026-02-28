"""
School Admin API endpoints for gradebook management.

Admin can create/update/delete grades on behalf of teachers.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.grade import GradeType
from app.api.dependencies import require_admin, get_current_user_school_id
from app.services.grade_service import GradeService
from app.schemas.grade import GradeCreate, GradeUpdate, GradeResponse

router = APIRouter(prefix="/grades", tags=["School Grades"])


@router.post(
    "",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a grade (admin)",
)
async def create_grade(
    data: GradeCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Admin creates a grade. teacher_id will be NULL."""
    service = GradeService(db)
    return await service.record_grade(
        data=data,
        school_id=school_id,
        user_id=current_user.id,
        teacher_id=None,
    )


@router.get(
    "/class/{class_id}/subject/{subject_id}",
    response_model=List[GradeResponse],
    summary="Get class journal (admin)",
)
async def get_class_journal(
    class_id: int,
    subject_id: int,
    quarter: Optional[int] = Query(None, ge=1, le=4),
    academic_year: Optional[str] = Query(None),
    grade_type: Optional[GradeType] = Query(None),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get class journal for admin view."""
    service = GradeService(db)
    return await service.get_class_journal(
        class_id=class_id,
        subject_id=subject_id,
        school_id=school_id,
        quarter=quarter,
        academic_year=academic_year,
        grade_type=grade_type,
    )


@router.get(
    "/student/{student_id}",
    response_model=List[GradeResponse],
    summary="Get student grades (admin)",
)
async def get_student_grades(
    student_id: int,
    subject_id: Optional[int] = Query(None),
    quarter: Optional[int] = Query(None, ge=1, le=4),
    academic_year: Optional[str] = Query(None),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get grades for a student. Admin can see any student in their school."""
    service = GradeService(db)
    if subject_id:
        return await service.get_student_subject_grades(
            student_id=student_id,
            subject_id=subject_id,
            school_id=school_id,
            quarter=quarter,
            academic_year=academic_year,
        )
    grades, _ = await service.get_student_grades(
        student_id=student_id,
        school_id=school_id,
        quarter=quarter,
        academic_year=academic_year,
    )
    return grades


@router.put(
    "/{grade_id}",
    response_model=GradeResponse,
    summary="Update a grade (admin)",
)
async def update_grade(
    grade_id: int,
    data: GradeUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing grade."""
    service = GradeService(db)
    return await service.update_grade(grade_id, data, school_id)


@router.delete(
    "/{grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a grade (admin)",
)
async def delete_grade(
    grade_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a grade."""
    service = GradeService(db)
    await service.delete_grade(grade_id, school_id)
