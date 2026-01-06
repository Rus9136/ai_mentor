"""
School Parent Management API for ADMIN.
"""

from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id, get_pagination_params
from app.models.user import User, UserRole
from app.models.parent import Parent
from app.repositories.user_repo import UserRepository
from app.repositories.parent_repo import ParentRepository
from app.core.security import get_password_hash
from app.schemas.parent import (
    ParentCreate,
    ParentResponse,
    ParentListResponse,
    AddChildrenRequest,
    StudentBriefResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from ._dependencies import get_parent_for_school_admin


router = APIRouter(prefix="/parents", tags=["School Parents"])


@router.get("", response_model=PaginatedResponse[ParentListResponse])
async def list_school_parents(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all parents for the school with pagination (ADMIN only).

    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **is_active**: Filter by active status
    """
    parent_repo = ParentRepository(db)

    parents, total = await parent_repo.get_all_paginated(
        school_id=school_id,
        page=pagination.page,
        page_size=pagination.page_size,
        is_active=is_active,
        load_user=True,
    )

    return PaginatedResponse.create(
        items=parents,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_school_parent(
    data: ParentCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new parent (ADMIN only).
    Creates both User and Parent in a transaction.
    Optionally links initial children (students).
    """
    user_repo = UserRepository(db)
    parent_repo = ParentRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {data.email} already exists"
        )

    # Create user first
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.PARENT,
        school_id=school_id,
        is_active=True
    )
    user = await user_repo.create(user)

    # Create parent
    parent = Parent(
        school_id=school_id,
        user_id=user.id
    )
    parent = await parent_repo.create(parent)

    # Add initial children if provided
    if data.student_ids:
        try:
            parent = await parent_repo.add_children(parent.id, data.student_ids)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Load user relationship
    parent = await parent_repo.get_by_id(parent.id, school_id, load_user=True, load_children=True)
    return parent


@router.get("/{parent_id}", response_model=ParentResponse)
async def get_school_parent(
    parent: Parent = Depends(get_parent_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific parent by ID (ADMIN only).
    """
    return parent


@router.delete("/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_parent(
    parent: Parent = Depends(get_parent_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a parent (ADMIN only).
    """
    parent_repo = ParentRepository(db)
    await parent_repo.soft_delete(parent)


# === Parent-Children Management ===

@router.get("/{parent_id}/children", response_model=List[StudentBriefResponse])
async def get_parent_children(
    parent_id: int,
    parent: Parent = Depends(get_parent_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all children (students) for a parent (ADMIN only).
    """
    parent_repo = ParentRepository(db)
    return await parent_repo.get_children(parent_id, school_id)


@router.post("/{parent_id}/children", response_model=ParentResponse)
async def add_parent_children(
    parent_id: int,
    data: AddChildrenRequest,
    parent: Parent = Depends(get_parent_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add children (students) to a parent (ADMIN only).
    """
    parent_repo = ParentRepository(db)

    try:
        parent = await parent_repo.add_children(parent_id, data.student_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    parent = await parent_repo.get_by_id(parent_id, school_id, load_user=True, load_children=True)
    return parent


@router.delete("/{parent_id}/children/{student_id}", response_model=ParentResponse)
async def remove_parent_child(
    parent_id: int,
    student_id: int,
    parent: Parent = Depends(get_parent_for_school_admin),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a child (student) from a parent (ADMIN only).
    """
    parent_repo = ParentRepository(db)

    try:
        parent = await parent_repo.remove_child(parent_id, student_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    parent = await parent_repo.get_by_id(parent_id, school_id, load_user=True, load_children=True)
    return parent
