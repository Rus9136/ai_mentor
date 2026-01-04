"""
School Teacher Management API for ADMIN.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User, UserRole
from app.models.teacher import Teacher
from app.repositories.user_repo import UserRepository
from app.repositories.teacher_repo import TeacherRepository
from app.repositories.goso_repo import GosoRepository
from app.core.security import get_password_hash
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherListResponse,
)
from ._dependencies import get_teacher_for_school_admin


router = APIRouter(prefix="/teachers", tags=["School Teachers"])


@router.get("", response_model=List[TeacherListResponse])
async def list_school_teachers(
    subject_id: Optional[int] = None,
    class_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all teachers for the school (ADMIN only).
    Optional filters: subject_id, class_id, is_active.
    """
    teacher_repo = TeacherRepository(db)

    if subject_id is not None or class_id is not None or is_active is not None:
        return await teacher_repo.get_by_filters(
            school_id,
            subject_id=subject_id,
            class_id=class_id,
            is_active=is_active,
            load_user=True
        )
    else:
        return await teacher_repo.get_all(school_id, load_user=True)


@router.post("", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_school_teacher(
    data: TeacherCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new teacher (ADMIN only).
    Creates both User and Teacher in a transaction.
    """
    user_repo = UserRepository(db)
    teacher_repo = TeacherRepository(db)
    goso_repo = GosoRepository(db)

    # Validate subject_id if provided
    subject_name = None
    if data.subject_id:
        subject = await goso_repo.get_subject_by_id(data.subject_id)
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {data.subject_id} not found"
            )
        subject_name = subject.name_ru

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {data.email} already exists"
        )

    # Check if teacher_code already exists (if provided)
    if data.teacher_code:
        existing_teacher = await teacher_repo.get_by_teacher_code(data.teacher_code, school_id)
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Teacher with code {data.teacher_code} already exists"
            )

    # Create user first
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.TEACHER,
        school_id=school_id,
        is_active=True
    )
    user = await user_repo.create(user)

    # Generate teacher_code if not provided
    teacher_code = data.teacher_code
    if not teacher_code:
        year = datetime.now().year % 100
        count = await teacher_repo.count_by_school(school_id)
        teacher_code = f"TCHR{year:02d}{count+1:04d}"

    # Create teacher
    teacher = Teacher(
        school_id=school_id,
        user_id=user.id,
        teacher_code=teacher_code,
        subject_id=data.subject_id,
        subject=subject_name,
        bio=data.bio
    )
    teacher = await teacher_repo.create(teacher)

    # Load user relationship and classes
    teacher = await teacher_repo.get_by_id(teacher.id, school_id, load_user=True, load_classes=True)
    return teacher


@router.get("/{teacher_id}", response_model=TeacherResponse)
async def get_school_teacher(
    teacher: Teacher = Depends(get_teacher_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific teacher by ID (ADMIN only).
    """
    return teacher


@router.put("/{teacher_id}", response_model=TeacherResponse)
async def update_school_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    teacher: Teacher = Depends(get_teacher_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update teacher info (ADMIN only).
    Can update: teacher_code, subject_id, bio.
    """
    teacher_repo = TeacherRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # If subject_id is being updated, validate and populate text field
    if "subject_id" in update_data and update_data["subject_id"] is not None:
        goso_repo = GosoRepository(db)
        subject = await goso_repo.get_subject_by_id(update_data["subject_id"])
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {update_data['subject_id']} not found"
            )
        update_data["subject"] = subject.name_ru

    for field, value in update_data.items():
        setattr(teacher, field, value)

    teacher = await teacher_repo.update(teacher)

    # Reload with relationships
    teacher = await teacher_repo.get_by_id(teacher_id, school_id, load_user=True, load_classes=True)
    return teacher


@router.delete("/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_teacher(
    teacher: Teacher = Depends(get_teacher_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a teacher (ADMIN only).
    """
    teacher_repo = TeacherRepository(db)
    await teacher_repo.soft_delete(teacher)
