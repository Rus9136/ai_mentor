"""
System settings models.
"""
from sqlalchemy import Column, String, Text, Boolean
from app.models.base import BaseModel


class SystemSetting(BaseModel):
    """System settings model."""

    __tablename__ = "system_settings"

    # Setting info
    key = Column(String(255), unique=True, nullable=False, index=True)
    value = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    is_public = Column(Boolean, default=False, nullable=False)  # Whether setting is exposed in API

    def __repr__(self) -> str:
        return f"<SystemSetting(key='{self.key}', value='{self.value}')>"
