"""
School Student Management API for ADMIN.
"""

from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User, UserRole
from app.models.student import Student
from app.repositories.user_repo import UserRepository
from app.repositories.student_repo import StudentRepository
from app.core.security import get_password_hash
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
)
from ._dependencies import get_student_for_school_admin


router = APIRouter(prefix="/students", tags=["School Students"])


@router.get("", response_model=List[StudentListResponse])
async def list_school_students(
    grade_level: Optional[int] = None,
    class_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all students for the school (ADMIN only).
    Optional filters: grade_level, class_id, is_active.
    """
    student_repo = StudentRepository(db)

    if grade_level is not None or class_id is not None or is_active is not None:
        return await student_repo.get_by_filters(
            school_id,
            grade_level=grade_level,
            class_id=class_id,
            is_active=is_active,
            load_user=True
        )
    else:
        return await student_repo.get_all(school_id, load_user=True)


@router.post("", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_school_student(
    data: StudentCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new student (ADMIN only).
    Creates both User and Student in a transaction.
    """
    user_repo = UserRepository(db)
    student_repo = StudentRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {data.email} already exists"
        )

    # Check if student_code already exists (if provided)
    if data.student_code:
        existing_student = await student_repo.get_by_student_code(data.student_code, school_id)
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student with code {data.student_code} already exists"
            )

    # Create user first
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.STUDENT,
        school_id=school_id,
        is_active=True
    )
    user = await user_repo.create(user)

    # Generate student_code if not provided
    student_code = data.student_code
    if not student_code:
        year = datetime.now().year % 100
        count = await student_repo.count_by_school(school_id)
        student_code = f"STU{data.grade_level}{year:02d}{count+1:04d}"

    # Create student
    student = Student(
        school_id=school_id,
        user_id=user.id,
        student_code=student_code,
        grade_level=data.grade_level,
        birth_date=data.birth_date
    )
    student = await student_repo.create(student)

    # Load user relationship and classes
    student = await student_repo.get_by_id(student.id, school_id, load_user=True, load_classes=True)
    return student


@router.get("/{student_id}", response_model=StudentResponse)
async def get_school_student(
    student: Student = Depends(get_student_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific student by ID (ADMIN only).
    """
    return student


@router.put("/{student_id}", response_model=StudentResponse)
async def update_school_student(
    student_id: int,
    data: StudentUpdate,
    student: Student = Depends(get_student_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student info (ADMIN only).
    Can update: student_code, grade_level, birth_date.
    """
    student_repo = StudentRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    student = await student_repo.update(student)

    # Reload with relationships
    student = await student_repo.get_by_id(student_id, school_id, load_user=True, load_classes=True)
    return student


@router.delete("/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_student(
    student: Student = Depends(get_student_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a student (ADMIN only).
    """
    student_repo = StudentRepository(db)
    await student_repo.soft_delete(student)
