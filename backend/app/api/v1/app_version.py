"""
Public endpoint for mobile app version checks.

GET /api/version — no authentication required.
"""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.app_version import AppVersion, Platform
from app.schemas.app_version import AppVersionResponse, PlatformEnum

router = APIRouter()


def is_version_lower(v1: str, v2: str) -> bool:
    """Return True if semver v1 < v2.  e.g. is_version_lower('1.0.0', '1.1.0') → True."""
    return tuple(map(int, v1.split("."))) < tuple(map(int, v2.split(".")))


@router.get("/version", response_model=AppVersionResponse)
async def get_app_version(
    platform: PlatformEnum = Query(..., description="Mobile platform (android / ios)"),
    current_version: str | None = Query(
        None,
        pattern=r"^\d+\.\d+\.\d+$",
        description="Client's current version for force_update check",
    ),
    db: AsyncSession = Depends(get_db),
):
    """
    Return latest version info for the given platform.

    `force_update` is True when the client's `current_version` is below `min_version`.
    """
    result = await db.execute(
        select(AppVersion).where(
            AppVersion.platform == Platform(platform.value),
            AppVersion.is_active.is_(True),
        )
    )
    version = result.scalars().first()

    if not version:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active version record for platform '{platform.value}'",
        )

    force_update = False
    if current_version:
        force_update = is_version_lower(current_version, version.min_version)

    return AppVersionResponse(
        latest_version=version.latest_version,
        min_version=version.min_version,
        force_update=force_update,
        release_notes=version.release_notes or "",
    )
