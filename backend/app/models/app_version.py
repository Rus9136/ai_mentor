"""
App version model for mobile client update checks.
"""

import enum

from sqlalchemy import Column, String, Text, Boolean, Enum

from app.models.base import BaseModel


class Platform(str, enum.Enum):
    """Supported mobile platforms."""

    ANDROID = "android"
    IOS = "ios"


class AppVersion(BaseModel):
    """Stores version info per platform for mobile update checks."""

    __tablename__ = "app_versions"

    platform = Column(
        Enum(Platform, values_callable=lambda e: [m.value for m in e]),
        nullable=False,
        index=True,
    )
    latest_version = Column(String(20), nullable=False)
    min_version = Column(String(20), nullable=False)
    release_notes = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    def __repr__(self) -> str:
        return f"<AppVersion(id={self.id}, platform='{self.platform}', latest='{self.latest_version}')>"
