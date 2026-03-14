"""
Pydantic schemas for School management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict, field_validator, EmailStr
import re


class AdminCredentials(BaseModel):
    """Admin user credentials for school creation."""

    email: EmailStr = Field(..., description="Admin email")
    password: str = Field(..., min_length=6, description="Admin password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")


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
    admin: Optional[AdminCredentials] = Field(None, description="Admin user to create with the school")

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


class SchoolAdminResponse(BaseModel):
    """Schema for school admin user info."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None
    is_active: bool
    created_at: datetime


class AdminPasswordReset(BaseModel):
    """Schema for resetting admin password."""

    password: str = Field(..., min_length=6, description="New password")


class SchoolListResponse(BaseModel):
    """Schema for school list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    is_active: bool
    email: Optional[str]
    created_at: datetime
