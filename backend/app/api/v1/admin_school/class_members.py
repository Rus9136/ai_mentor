"""
School Class Members (Students/Teachers) Management API for ADMIN.
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
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
    SetHomeroomRequest,
    ClassTeacherInfo,
)
from ._dependencies import get_class_for_school_admin


router = APIRouter(tags=["School Class Members"])


def _build_teacher_assignments(school_class: SchoolClass) -> list:
    """Build ClassTeacherInfo list from class_teachers relationship."""
    assignments = []
    for ct in school_class.class_teachers:
        teacher = ct.teacher
        user = teacher.user if teacher else None
        assignments.append(ClassTeacherInfo(
            id=ct.id,
            teacher_id=ct.teacher_id,
            teacher_code=teacher.teacher_code if teacher else "",
            first_name=user.first_name if user else "",
            last_name=user.last_name if user else "",
            middle_name=user.middle_name if user else None,
            email=user.email if user else None,
            subject_id=ct.subject_id,
            subject_name=ct.subject.name_ru if ct.subject else None,
            is_homeroom=ct.is_homeroom,
        ))
    return assignments


async def _reload_class_with_assignments(
    class_repo: SchoolClassRepository,
    class_id: int,
    school_id: int,
) -> SchoolClassResponse:
    """Reload class and build response with teacher_assignments."""
    school_class = await class_repo.get_by_id(
        class_id, school_id, load_students=True, load_teachers=True
    )
    response = SchoolClassResponse.model_validate(school_class)
    response.teacher_assignments = _build_teacher_assignments(school_class)
    return response


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
    """Add students to a class (bulk operation, ADMIN only)."""
    class_repo = SchoolClassRepository(db)

    try:
        await class_repo.add_students(class_id, data.student_ids, school_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return await _reload_class_with_assignments(class_repo, class_id, school_id)


@router.delete("/classes/{class_id}/students/{student_id}", response_model=SchoolClassResponse)
async def remove_student_from_class(
    class_id: int,
    student_id: int,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove a student from a class (ADMIN only)."""
    class_repo = SchoolClassRepository(db)
    await class_repo.remove_students(class_id, [student_id], school_id)
    return await _reload_class_with_assignments(class_repo, class_id, school_id)


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
    Add teachers to a class with subject assignments (ADMIN only).

    Request body: {"assignments": [{"teacher_id": 1, "subject_id": 5, "is_homeroom": false}]}
    """
    class_repo = SchoolClassRepository(db)

    try:
        await class_repo.add_teachers(class_id, data.assignments, school_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return await _reload_class_with_assignments(class_repo, class_id, school_id)


@router.delete("/classes/{class_id}/teachers/{teacher_id}", response_model=SchoolClassResponse)
async def remove_teacher_from_class(
    class_id: int,
    teacher_id: int,
    subject_id: Optional[int] = Query(None, description="Remove only this subject assignment"),
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a teacher from a class (ADMIN only).

    If subject_id is provided, removes only that specific subject assignment.
    Otherwise removes all assignments for this teacher in this class.
    """
    class_repo = SchoolClassRepository(db)

    if subject_id is not None:
        await class_repo.remove_teachers(class_id, [teacher_id], school_id, subject_id=subject_id)
    else:
        await class_repo.remove_teachers(class_id, [teacher_id], school_id)

    return await _reload_class_with_assignments(class_repo, class_id, school_id)


@router.put("/classes/{class_id}/homeroom", response_model=SchoolClassResponse)
async def set_homeroom_teacher(
    class_id: int,
    data: SetHomeroomRequest,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Set a teacher as homeroom (классный руководитель) for a class."""
    class_repo = SchoolClassRepository(db)

    try:
        school_class = await class_repo.set_homeroom_teacher(
            class_id, data.teacher_id, school_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    response = SchoolClassResponse.model_validate(school_class)
    response.teacher_assignments = _build_teacher_assignments(school_class)
    return response


@router.delete("/classes/{class_id}/homeroom", response_model=SchoolClassResponse)
async def unset_homeroom_teacher(
    class_id: int,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Remove homeroom teacher designation from a class."""
    class_repo = SchoolClassRepository(db)
    school_class = await class_repo.unset_homeroom_teacher(class_id, school_id)
    response = SchoolClassResponse.model_validate(school_class)
    response.teacher_assignments = _build_teacher_assignments(school_class)
    return response
