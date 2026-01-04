"""
School User Management API for ADMIN.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import UserResponseSchema, UserUpdate
from ._dependencies import get_user_for_school_admin


router = APIRouter(prefix="/users", tags=["School Users"])


@router.get("", response_model=List[UserResponseSchema])
async def list_school_users(
    role: Optional[str] = None,
    is_active: Optional[bool] = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users for the school (ADMIN only).
    Optional filters: role, is_active.
    """
    user_repo = UserRepository(db)
    return await user_repo.get_by_school(school_id, role=role, is_active=is_active)


@router.get("/{user_id}", response_model=UserResponseSchema)
async def get_school_user(
    user: User = Depends(get_user_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific user by ID (ADMIN only).
    """
    return user


@router.put("/{user_id}", response_model=UserResponseSchema)
async def update_school_user(
    data: UserUpdate,
    user: User = Depends(get_user_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user info (ADMIN only).
    Can update: first_name, last_name, middle_name, phone.
    Cannot update: email, password, role.
    """
    user_repo = UserRepository(db)

    # Update only allowed fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    return await user_repo.update(user)


@router.post("/{user_id}/deactivate", response_model=UserResponseSchema)
async def deactivate_school_user(
    user: User = Depends(get_user_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user (set is_active=False) (ADMIN only).
    """
    user_repo = UserRepository(db)
    return await user_repo.deactivate(user)


@router.post("/{user_id}/activate", response_model=UserResponseSchema)
async def activate_school_user(
    user: User = Depends(get_user_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a user (set is_active=True) (ADMIN only).
    """
    user_repo = UserRepository(db)
    return await user_repo.activate(user)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_user(
    user: User = Depends(get_user_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a user (ADMIN only).
    """
    user_repo = UserRepository(db)
    await user_repo.soft_delete(user)
