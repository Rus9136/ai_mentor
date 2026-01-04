"""
School Settings Management API for ADMIN.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.repositories.school_repo import SchoolRepository
from app.schemas.school import SchoolUpdate, SchoolResponse


router = APIRouter(prefix="/settings", tags=["School Settings"])


@router.get("", response_model=SchoolResponse)
async def get_school_settings(
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get settings for the current school (ADMIN only).
    Returns the school information including contact details.
    """
    school_repo = SchoolRepository(db)

    school = await school_repo.get_by_id(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found"
        )

    return school


@router.put("", response_model=SchoolResponse)
async def update_school_settings(
    data: SchoolUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update settings for the current school (ADMIN only).

    School ADMIN can update:
    - description
    - email
    - phone
    - address

    School ADMIN CANNOT update:
    - name (only SUPER_ADMIN)
    - code (only SUPER_ADMIN)
    - is_active (only SUPER_ADMIN)
    """
    school_repo = SchoolRepository(db)

    school = await school_repo.get_by_id(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found"
        )

    # School ADMIN can only update certain fields
    update_data = data.model_dump(exclude_unset=True)

    # Remove restricted fields if present
    restricted_fields = {"name", "code", "is_active"}
    for field in restricted_fields:
        update_data.pop(field, None)

    # Apply updates
    for key, value in update_data.items():
        setattr(school, key, value)

    updated_school = await school_repo.update(school)
    return updated_school
