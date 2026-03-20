"""
Global User Management API for SUPER_ADMIN.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin, get_pagination_params
from app.models.user import User
from app.repositories.user_repo import UserRepository
from app.schemas.user import GlobalUserListResponse
from app.schemas.pagination import PaginatedResponse, PaginationParams


router = APIRouter(prefix="/users", tags=["Global Users"])


@router.get("", response_model=PaginatedResponse[GlobalUserListResponse])
async def list_all_users(
    role: Optional[str] = Query(None, description="Filter by role (super_admin, admin, teacher, student, parent)"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Search by name, email, or phone"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all users across all schools with pagination (SUPER_ADMIN only).

    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **role**: Filter by role
    - **is_active**: Filter by active status
    - **search**: Search by name, email, or phone
    """
    user_repo = UserRepository(db)

    users, total = await user_repo.get_all_paginated(
        page=pagination.page,
        page_size=pagination.page_size,
        role=role,
        is_active=is_active,
        search=search,
    )

    items = []
    for user in users:
        items.append(
            GlobalUserListResponse(
                id=user.id,
                email=user.email,
                role=user.role.value if hasattr(user.role, 'value') else user.role,
                school_id=user.school_id,
                school_name=user.school.name if user.school else None,
                first_name=user.first_name,
                last_name=user.last_name,
                middle_name=user.middle_name,
                phone=user.phone,
                is_active=user.is_active,
                is_verified=user.is_verified,
                auth_provider=user.auth_provider.value if hasattr(user.auth_provider, 'value') else user.auth_provider,
                created_at=user.created_at,
            )
        )

    return PaginatedResponse.create(
        items=items,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )
