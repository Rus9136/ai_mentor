"""
Teacher API endpoints for school gradebook (journal).

All endpoints require TEACHER role.
"""
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.models.teacher import Teacher
from app.api.dependencies import require_teacher, get_current_user_school_id
from app.services.grade_service import GradeService
from app.models.grade import GradeType
from app.schemas.grade import (
    GradeCreate,
    GradeUpdate,
    GradeResponse,
    GradeWithDetailsResponse,
)

router = APIRouter()


def _to_detail(grade) -> dict:
    """Convert Grade to GradeWithDetailsResponse data."""
    data = {
        "id": grade.id,
        "student_id": grade.student_id,
        "school_id": grade.school_id,
        "subject_id": grade.subject_id,
        "class_id": grade.class_id,
        "teacher_id": grade.teacher_id,
        "grade_value": grade.grade_value,
        "grade_type": grade.grade_type,
        "grade_date": grade.grade_date,
        "quarter": grade.quarter,
        "academic_year": grade.academic_year,
        "comment": grade.comment,
        "created_at": grade.created_at,
        "student_name": None,
        "subject_name": None,
    }
    if grade.student and grade.student.user_id:
        # Student relationship is loaded with joined
        pass
    if grade.subject:
        data["subject_name"] = grade.subject.name_ru
    return data


@router.post(
    "/teachers/grades",
    response_model=GradeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a grade",
)
async def create_grade(
    data: GradeCreate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Record a new grade for a student. Teacher must belong to the same school."""
    # Resolve teacher_id
    result = await db.execute(
        select(Teacher).where(
            Teacher.user_id == current_user.id,
            Teacher.school_id == school_id,
        )
    )
    teacher = result.scalar_one_or_none()
    teacher_id = teacher.id if teacher else None

    service = GradeService(db)
    grade = await service.record_grade(
        data=data,
        school_id=school_id,
        user_id=current_user.id,
        teacher_id=teacher_id,
    )
    return grade


@router.get(
    "/teachers/grades/class/{class_id}/subject/{subject_id}",
    response_model=List[GradeResponse],
    summary="Get class journal",
)
async def get_class_journal(
    class_id: int,
    subject_id: int,
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter (1-4)"),
    academic_year: Optional[str] = Query(None, description="Academic year, e.g. 2025-2026"),
    grade_type: Optional[GradeType] = Query(None, description="Grade type filter"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get all grades for a class in a subject. Journal view for the teacher."""
    service = GradeService(db)
    grades = await service.get_class_journal(
        class_id=class_id,
        subject_id=subject_id,
        school_id=school_id,
        quarter=quarter,
        academic_year=academic_year,
        grade_type=grade_type,
    )
    return grades


@router.get(
    "/teachers/grades/student/{student_id}",
    response_model=List[GradeResponse],
    summary="Get student grades",
)
async def get_student_grades(
    student_id: int,
    subject_id: Optional[int] = Query(None, description="Filter by subject"),
    quarter: Optional[int] = Query(None, ge=1, le=4, description="Quarter (1-4)"),
    academic_year: Optional[str] = Query(None, description="Academic year"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get grades for a specific student. Teacher can see any student in their school."""
    service = GradeService(db)
    if subject_id:
        grades = await service.get_student_subject_grades(
            student_id=student_id,
            subject_id=subject_id,
            school_id=school_id,
            quarter=quarter,
            academic_year=academic_year,
        )
    else:
        grades, _ = await service.get_student_grades(
            student_id=student_id,
            school_id=school_id,
            quarter=quarter,
            academic_year=academic_year,
        )
    return grades


@router.put(
    "/teachers/grades/{grade_id}",
    response_model=GradeResponse,
    summary="Update a grade",
)
async def update_grade(
    grade_id: int,
    data: GradeUpdate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing grade."""
    service = GradeService(db)
    return await service.update_grade(grade_id, data, school_id)


@router.delete(
    "/teachers/grades/{grade_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a grade",
)
async def delete_grade(
    grade_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a grade."""
    service = GradeService(db)
    await service.delete_grade(grade_id, school_id)
