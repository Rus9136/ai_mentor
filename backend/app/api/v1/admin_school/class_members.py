"""
School Class Members (Students/Teachers) Management API for ADMIN.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.school_class import SchoolClass
from app.repositories.school_class_repo import SchoolClassRepository
from app.schemas.school_class import (
    SchoolClassResponse,
    AddStudentsRequest,
    AddTeachersRequest,
)
from ._dependencies import get_class_for_school_admin


router = APIRouter(tags=["School Class Members"])


# === Students Management ===

@router.post("/classes/{class_id}/students", response_model=SchoolClassResponse)
async def add_students_to_class(
    class_id: int,
    data: AddStudentsRequest,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add students to a class (bulk operation, ADMIN only).
    """
    class_repo = SchoolClassRepository(db)

    try:
        await class_repo.add_students(class_id, data.student_ids, school_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)
    return school_class


@router.delete("/classes/{class_id}/students/{student_id}", response_model=SchoolClassResponse)
async def remove_student_from_class(
    class_id: int,
    student_id: int,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a student from a class (ADMIN only).
    """
    class_repo = SchoolClassRepository(db)

    await class_repo.remove_students(class_id, [student_id], school_id)

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)
    return school_class


# === Teachers Management ===

@router.post("/classes/{class_id}/teachers", response_model=SchoolClassResponse)
async def add_teachers_to_class(
    class_id: int,
    data: AddTeachersRequest,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add teachers to a class (bulk operation, ADMIN only).
    """
    class_repo = SchoolClassRepository(db)

    try:
        await class_repo.add_teachers(class_id, data.teacher_ids, school_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)
    return school_class


@router.delete("/classes/{class_id}/teachers/{teacher_id}", response_model=SchoolClassResponse)
async def remove_teacher_from_class(
    class_id: int,
    teacher_id: int,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a teacher from a class (ADMIN only).
    """
    class_repo = SchoolClassRepository(db)

    await class_repo.remove_teachers(class_id, [teacher_id], school_id)

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)
    return school_class
