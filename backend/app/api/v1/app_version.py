"""
Public endpoint for mobile app version checks.

GET  /api/version        — no authentication required.
POST /api/version/deploy — secured by DEPLOY_API_KEY, called from build scripts.
"""

import logging

from fastapi import APIRouter, Depends, Header, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.app_version import AppVersion, Platform
from app.schemas.app_version import AppVersionDeploy, AppVersionResponse, PlatformEnum

logger = logging.getLogger(__name__)

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


@router.post("/version/deploy", response_model=AppVersionResponse)
async def deploy_version(
    data: AppVersionDeploy,
    x_deploy_key: str = Header(..., description="DEPLOY_API_KEY from .env"),
    db: AsyncSession = Depends(get_db),
):
    """
    Update latest_version for a platform. Called from Flutter build scripts.

    Secured by X-Deploy-Key header (matches DEPLOY_API_KEY in .env).
    """
    if not settings.DEPLOY_API_KEY or x_deploy_key != settings.DEPLOY_API_KEY:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Invalid deploy key")

    result = await db.execute(
        select(AppVersion).where(
            AppVersion.platform == Platform(data.platform.value),
            AppVersion.is_active.is_(True),
        )
    )
    version = result.scalars().first()

    if not version:
        # Create new record if none exists
        version = AppVersion(
            platform=Platform(data.platform.value),
            latest_version=data.version,
            min_version=data.min_version or data.version,
            release_notes=data.release_notes,
            is_active=True,
        )
        db.add(version)
    else:
        version.latest_version = data.version
        if data.min_version:
            version.min_version = data.min_version
        if data.release_notes is not None:
            version.release_notes = data.release_notes

    await db.flush()
    await db.refresh(version)

    logger.info(
        "Deploy version update: platform=%s version=%s min=%s",
        data.platform.value, data.version, version.min_version,
    )

    return AppVersionResponse(
        latest_version=version.latest_version,
        min_version=version.min_version,
        force_update=False,
        release_notes=version.release_notes or "",
    )
