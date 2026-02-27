"""
Pydantic schemas for app version endpoints.
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class PlatformEnum(str, Enum):
    android = "android"
    ios = "ios"


# --- Public response ---


class AppVersionResponse(BaseModel):
    """Public response for GET /api/version."""

    latest_version: str
    min_version: str
    force_update: bool
    release_notes: Optional[str] = None


# --- Admin schemas ---


class AppVersionAdminCreate(BaseModel):
    """Create / update a version record (SUPER_ADMIN)."""

    platform: PlatformEnum
    latest_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", examples=["1.2.0"])
    min_version: str = Field(..., pattern=r"^\d+\.\d+\.\d+$", examples=["1.0.0"])
    release_notes: Optional[str] = None


class AppVersionAdminResponse(BaseModel):
    """Full version record returned to admin."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    platform: PlatformEnum
    latest_version: str
    min_version: str
    release_notes: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime
