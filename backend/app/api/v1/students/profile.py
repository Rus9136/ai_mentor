"""
Student Profile API endpoint.

Provides endpoint for students to view their profile with class information,
and to create join requests to classes.
"""

from typing import Optional, List
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import require_student
from app.core.database import get_db
from app.models.student import Student
from app.models.user import User
from app.schemas.join_request import (
    StudentJoinRequestCreate,
    StudentJoinRequestStatusResponse,
    JoinRequestResponse,
)
from app.services.join_request_service import JoinRequestService


router = APIRouter()


# =============================================================================
# Response Schemas
# =============================================================================


class ClassInfo(BaseModel):
    """Brief class information for profile."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    grade_level: int


class StudentProfileResponse(BaseModel):
    """Student profile with class information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_code: str
    grade_level: int
    birth_date: Optional[date] = None
    school_name: Optional[str] = None
    classes: List[ClassInfo] = []


# =============================================================================
# Endpoints
# =============================================================================


@router.get("/profile", response_model=StudentProfileResponse)
async def get_student_profile(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current student's profile with class information.

    Returns:
    - student_code: Unique student identifier
    - grade_level: Grade level (1-11)
    - birth_date: Date of birth (if set)
    - classes: List of classes the student is enrolled in
    """
    result = await db.execute(
        select(Student)
        .where(Student.user_id == current_user.id)
        .options(selectinload(Student.classes), selectinload(Student.school))
    )
    student = result.scalar_one_or_none()

    if not student:
        # Return empty profile if student record not found
        return StudentProfileResponse(
            id=0,
            student_code="",
            grade_level=0,
            classes=[],
        )

    return StudentProfileResponse(
        id=student.id,
        student_code=student.student_code,
        grade_level=student.grade_level,
        birth_date=student.birth_date,
        school_name=student.school.name if student.school else None,
        classes=[
            ClassInfo(
                id=cls.id,
                name=cls.name,
                grade_level=cls.grade_level,
            )
            for cls in student.classes
        ],
    )


# =============================================================================
# Join Request Endpoints
# =============================================================================

ERROR_MESSAGES = {
    "code_not_found": "Код приглашения не найден",
    "code_expired": "Срок действия кода истёк",
    "code_exhausted": "Код использован максимальное количество раз",
    "code_inactive": "Код приглашения неактивен",
    "request_pending": "У вас уже есть активная заявка на рассмотрении",
    "already_in_class": "Вы уже состоите в этом классе",
    "no_class": "Код не привязан к классу",
}


@router.post("/join-request", response_model=JoinRequestResponse)
async def create_join_request(
    data: StudentJoinRequestCreate,
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a join request to a class using invitation code.

    The student provides:
    - invitation_code: Code from the teacher
    - first_name, last_name, middle_name: FIO to use in the class

    The request will be pending until the teacher approves it.
    Upon approval, the student's school and class will be updated.
    """
    # Get student record
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student record not found"
        )

    # Create join request
    service = JoinRequestService(db)
    request, error_code = await service.create_request_by_code(
        student_id=student.id,
        invitation_code=data.invitation_code,
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name
    )

    if error_code:
        error_message = ERROR_MESSAGES.get(error_code, error_code)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error_message
        )

    return JoinRequestResponse(
        id=request.id,
        student_id=request.student_id,
        class_id=request.class_id,
        school_id=request.school_id,
        status=request.status.value,
        created_at=request.created_at,
    )


@router.get("/join-request/status", response_model=StudentJoinRequestStatusResponse)
async def get_join_request_status(
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Get current student's join request status.

    Returns the latest pending or rejected request, if any.
    Used to show the request status in the student profile.
    """
    # Get student record
    result = await db.execute(
        select(Student).where(Student.user_id == current_user.id)
    )
    student = result.scalar_one_or_none()

    if not student:
        return StudentJoinRequestStatusResponse(has_request=False)

    service = JoinRequestService(db)
    return await service.get_student_request_status(student.id)
