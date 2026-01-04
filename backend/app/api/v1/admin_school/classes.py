"""
School Class Management API for ADMIN.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.school_class import SchoolClass
from app.repositories.school_class_repo import SchoolClassRepository
from app.schemas.school_class import (
    SchoolClassCreate,
    SchoolClassUpdate,
    SchoolClassResponse,
    SchoolClassListResponse,
)
from ._dependencies import get_class_for_school_admin


router = APIRouter(prefix="/classes", tags=["School Classes"])


@router.get("", response_model=List[SchoolClassListResponse])
async def list_school_classes(
    grade_level: Optional[int] = None,
    academic_year: Optional[str] = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all classes for the school (ADMIN only).
    Optional filters: grade_level, academic_year.
    """
    class_repo = SchoolClassRepository(db)

    if grade_level is not None or academic_year is not None:
        classes = await class_repo.get_by_filters(
            school_id,
            grade_level=grade_level,
            academic_year=academic_year,
            load_students=True,
            load_teachers=True
        )
    else:
        classes = await class_repo.get_all(school_id, load_students=True, load_teachers=True)

    # Add counts for response
    result = []
    for school_class in classes:
        class_dict = {
            "id": school_class.id,
            "name": school_class.name,
            "code": school_class.code,
            "grade_level": school_class.grade_level,
            "academic_year": school_class.academic_year,
            "students_count": len(school_class.students) if school_class.students else 0,
            "teachers_count": len(school_class.teachers) if school_class.teachers else 0,
            "created_at": school_class.created_at,
        }
        result.append(class_dict)

    return result


@router.post("", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
async def create_school_class(
    data: SchoolClassCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new school class (ADMIN only).
    """
    class_repo = SchoolClassRepository(db)

    # Check if code already exists in this school
    existing_class = await class_repo.get_by_code(data.code, school_id)
    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Class with code {data.code} already exists in this school"
        )

    # Create class
    school_class = SchoolClass(
        school_id=school_id,
        name=data.name,
        code=data.code,
        grade_level=data.grade_level,
        academic_year=data.academic_year
    )
    school_class = await class_repo.create(school_class)

    # Return with counts
    return {
        "id": school_class.id,
        "school_id": school_class.school_id,
        "name": school_class.name,
        "code": school_class.code,
        "grade_level": school_class.grade_level,
        "academic_year": school_class.academic_year,
        "created_at": school_class.created_at,
        "updated_at": school_class.updated_at,
        "students_count": 0,
        "teachers_count": 0,
    }


@router.get("/{class_id}", response_model=SchoolClassResponse)
async def get_school_class(
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific class by ID (ADMIN only).
    Includes students and teachers lists.
    """
    return school_class


@router.put("/{class_id}", response_model=SchoolClassResponse)
async def update_school_class(
    class_id: int,
    data: SchoolClassUpdate,
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update class info (ADMIN only).
    Can update: name, grade_level, academic_year.
    Note: code is NOT updatable.
    """
    class_repo = SchoolClassRepository(db)

    # Update fields
    if data.name is not None:
        school_class.name = data.name
    if data.grade_level is not None:
        school_class.grade_level = data.grade_level
    if data.academic_year is not None:
        school_class.academic_year = data.academic_year

    await class_repo.update(school_class)

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)
    return school_class


@router.delete("/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_class(
    school_class: SchoolClass = Depends(get_class_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a class (ADMIN only).
    """
    class_repo = SchoolClassRepository(db)
    await class_repo.soft_delete(school_class)
