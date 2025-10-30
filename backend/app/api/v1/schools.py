"""
Schools management API for SUPER_ADMIN.
Manages schools (tenants) in the multi-tenant system.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.school import School
from app.repositories.school_repo import SchoolRepository
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse,
)

router = APIRouter()


@router.get("/schools", response_model=List[SchoolListResponse])
async def list_schools(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all schools (SUPER_ADMIN only).
    Returns list of all schools ordered by creation date (newest first).
    """
    school_repo = SchoolRepository(db)
    return await school_repo.get_all()


@router.post(
    "/schools", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED
)
async def create_school(
    data: SchoolCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new school (SUPER_ADMIN only).

    Validates:
    - Code must be unique across all schools
    - Code format: lowercase alphanumeric with dashes/underscores
    """
    school_repo = SchoolRepository(db)

    # Check if code already exists
    existing_school = await school_repo.get_by_code(data.code)
    if existing_school:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"School with code '{data.code}' already exists",
        )

    # Create new school
    school = School(**data.model_dump(), is_active=True)
    return await school_repo.create(school)


@router.get("/schools/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific school by ID (SUPER_ADMIN only).
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    return school


@router.put("/schools/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: int,
    data: SchoolUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a school (SUPER_ADMIN only).

    Note: School code cannot be updated after creation.
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)

    return await school_repo.update(school)


@router.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a school (SUPER_ADMIN only).

    Sets is_deleted=True and deleted_at timestamp.
    This is a soft delete - data is not physically removed.
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    await school_repo.soft_delete(school)


@router.patch("/schools/{school_id}/block", response_model=SchoolResponse)
async def block_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Block a school (SUPER_ADMIN only).

    Sets is_active=False to prevent school users from accessing the system.
    """
    school_repo = SchoolRepository(db)

    try:
        school = await school_repo.block(school_id)
        return school
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/schools/{school_id}/unblock", response_model=SchoolResponse)
async def unblock_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unblock a school (SUPER_ADMIN only).

    Sets is_active=True to restore school access.
    """
    school_repo = SchoolRepository(db)

    try:
        school = await school_repo.unblock(school_id)
        return school
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
