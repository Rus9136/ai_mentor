"""
Admin endpoints for managing app version records (SUPER_ADMIN only).
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.app_version import AppVersion, Platform
from app.schemas.app_version import (
    AppVersionAdminCreate,
    AppVersionAdminResponse,
)

router = APIRouter()


@router.get("/app-versions", response_model=list[AppVersionAdminResponse])
async def list_app_versions(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all app version records."""
    result = await db.execute(select(AppVersion).order_by(AppVersion.id))
    return result.scalars().all()


@router.post(
    "/app-versions",
    response_model=AppVersionAdminResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_or_update_app_version(
    data: AppVersionAdminCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create or update the active version record for a platform.

    If an active record already exists for the platform it is deactivated
    and a new active record is created (keeps history).
    """
    # Deactivate existing active record for this platform
    result = await db.execute(
        select(AppVersion).where(
            AppVersion.platform == Platform(data.platform.value),
            AppVersion.is_active.is_(True),
        )
    )
    existing = result.scalars().first()
    if existing:
        existing.is_active = False

    # Create new active record
    version = AppVersion(
        platform=Platform(data.platform.value),
        latest_version=data.latest_version,
        min_version=data.min_version,
        release_notes=data.release_notes,
        is_active=True,
    )
    db.add(version)
    await db.flush()
    await db.refresh(version)
    return version
