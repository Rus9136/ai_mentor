"""
Pydantic schemas for School management.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class SchoolCreate(BaseModel):
    """Schema for creating a new school."""

    name: str = Field(..., min_length=1, max_length=255, description="School name")
    code: str = Field(
        ...,
        min_length=2,
        max_length=50,
        description="School code (unique identifier, lowercase alphanumeric with dashes/underscores)",
    )
    description: Optional[str] = Field(None, description="School description")
    email: Optional[str] = Field(None, max_length=255, description="School email")
    phone: Optional[str] = Field(None, max_length=50, description="School phone")
    address: Optional[str] = Field(None, description="School address")

    @field_validator("code")
    @classmethod
    def validate_code(cls, v: str) -> str:
        """Validate that code contains only lowercase alphanumeric characters, dashes, and underscores."""
        if not re.match(r"^[a-z0-9_-]+$", v):
            raise ValueError(
                "Code must contain only lowercase letters, numbers, dashes, and underscores"
            )
        return v


class SchoolUpdate(BaseModel):
    """Schema for updating an existing school."""

    name: Optional[str] = Field(
        None, min_length=1, max_length=255, description="School name"
    )
    description: Optional[str] = Field(None, description="School description")
    email: Optional[str] = Field(None, max_length=255, description="School email")
    phone: Optional[str] = Field(None, max_length=50, description="School phone")
    address: Optional[str] = Field(None, description="School address")
    # Note: code is NOT updatable


class SchoolResponse(BaseModel):
    """Schema for school response (detailed)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    description: Optional[str]
    is_active: bool
    email: Optional[str]
    phone: Optional[str]
    address: Optional[str]
    created_at: datetime
    updated_at: datetime


class SchoolListResponse(BaseModel):
    """Schema for school list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    is_active: bool
    email: Optional[str]
    created_at: datetime
