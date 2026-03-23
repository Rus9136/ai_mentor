"""
School Teacher Management API for ADMIN.
"""

from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id, get_pagination_params
from app.models.user import User, UserRole, AuthProvider
from app.models.teacher import Teacher
from app.models.teacher_subject import TeacherSubject
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
from app.schemas.pagination import PaginatedResponse, PaginationParams
from ._dependencies import get_teacher_for_school_admin


router = APIRouter(prefix="/teachers", tags=["School Teachers"])


@router.get("", response_model=PaginatedResponse[TeacherListResponse])
async def list_school_teachers(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, min_length=2, description="Search by name or email"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all teachers for the school with pagination (ADMIN only).

    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **subject_id**: Filter by subject
    - **class_id**: Filter by class
    - **is_active**: Filter by active status
    - **search**: Search by first_name, last_name, or email (min 2 chars)
    """
    teacher_repo = TeacherRepository(db)

    teachers, total = await teacher_repo.get_all_paginated(
        school_id=school_id,
        page=pagination.page,
        page_size=pagination.page_size,
        subject_id=subject_id,
        class_id=class_id,
        is_active=is_active,
        search=search,
        load_user=True,
    )

    return PaginatedResponse.create(
        items=teachers,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


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

    # Resolve subject IDs: prefer subject_ids (new), fall back to subject_id (legacy)
    resolved_subject_ids = []
    if data.subject_ids:
        for sid in data.subject_ids:
            subj = await goso_repo.get_subject_by_id(sid)
            if not subj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject with ID {sid} not found"
                )
            resolved_subject_ids.append(subj)
    elif data.subject_id:
        subj = await goso_repo.get_subject_by_id(data.subject_id)
        if not subj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {data.subject_id} not found"
            )
        resolved_subject_ids.append(subj)

    # Legacy fields: first subject for backward compat
    first_subject_id = resolved_subject_ids[0].id if resolved_subject_ids else None
    subject_name = resolved_subject_ids[0].name_ru if resolved_subject_ids else None

    # Check if email already exists
    email = data.email
    if email:
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email {email} already exists"
            )
    else:
        # Phone-only teacher — generate synthetic email
        email = f"phone_{data.phone}@phone.local"
        existing_user = await user_repo.get_by_email(email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with phone {data.phone} already exists"
            )

    # Check phone uniqueness
    if data.phone:
        existing_phone_user = await user_repo.get_by_phone(data.phone)
        if existing_phone_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with phone {data.phone} already exists"
            )

    # Check if teacher_code already exists (if provided)
    if data.teacher_code:
        existing_teacher = await teacher_repo.get_by_teacher_code(data.teacher_code, school_id)
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Teacher with code {data.teacher_code} already exists"
            )

    # Determine auth provider
    auth_provider = AuthProvider.PHONE if not data.email and data.phone else AuthProvider.LOCAL

    # Create user first
    user = User(
        email=email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.TEACHER,
        school_id=school_id,
        is_active=True,
        auth_provider=auth_provider,
    )
    user = await user_repo.create(user)

    # Generate teacher_code if not provided
    teacher_code = data.teacher_code
    if not teacher_code:
        year = datetime.now().year % 100
        count = await teacher_repo.count_by_school(school_id)
        teacher_code = f"TCHR{year:02d}{count+1:04d}"

    # Create teacher (legacy subject_id = first subject for backward compat)
    teacher = Teacher(
        school_id=school_id,
        user_id=user.id,
        teacher_code=teacher_code,
        subject_id=first_subject_id,
        subject=subject_name,
        bio=data.bio
    )
    teacher = await teacher_repo.create(teacher)

    # Create junction table entries for multi-subject
    for subj in resolved_subject_ids:
        ts = TeacherSubject(teacher_id=teacher.id, subject_id=subj.id)
        db.add(ts)
    if resolved_subject_ids:
        await db.commit()

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
    goso_repo = GosoRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # Handle multi-subject update
    if "subject_ids" in update_data and update_data["subject_ids"] is not None:
        new_subject_ids = update_data.pop("subject_ids")
        # Validate all subject IDs
        resolved_subjects = []
        for sid in new_subject_ids:
            subj = await goso_repo.get_subject_by_id(sid)
            if not subj:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Subject with ID {sid} not found"
                )
            resolved_subjects.append(subj)

        # Replace junction table entries
        from sqlalchemy import delete
        await db.execute(
            delete(TeacherSubject).where(TeacherSubject.teacher_id == teacher.id)
        )
        for subj in resolved_subjects:
            db.add(TeacherSubject(teacher_id=teacher.id, subject_id=subj.id))

        # Update legacy fields for backward compat
        if resolved_subjects:
            update_data["subject_id"] = resolved_subjects[0].id
            update_data["subject"] = resolved_subjects[0].name_ru
        else:
            update_data["subject_id"] = None
            update_data["subject"] = None
    elif "subject_id" in update_data and update_data["subject_id"] is not None:
        # Legacy single subject update — also update junction table
        subj = await goso_repo.get_subject_by_id(update_data["subject_id"])
        if not subj:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {update_data['subject_id']} not found"
            )
        update_data["subject"] = subj.name_ru

        from sqlalchemy import delete
        await db.execute(
            delete(TeacherSubject).where(TeacherSubject.teacher_id == teacher.id)
        )
        db.add(TeacherSubject(teacher_id=teacher.id, subject_id=subj.id))

    # Remove subject_ids from update_data if still present (not a model column)
    update_data.pop("subject_ids", None)

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
