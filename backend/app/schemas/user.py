"""
Pydantic schemas for User management.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict


class UserCreate(BaseModel):
    """Schema for creating a new user."""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=8, description="User password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    role: str = Field(..., description="User role (admin, teacher, student, parent)")


class UserUpdate(BaseModel):
    """Schema for updating an existing user."""

    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    # Note: email and role are NOT updatable


class UserResponseSchema(BaseModel):
    """Schema for user response (detailed)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    school_id: Optional[int]
    first_name: str
    last_name: str
    middle_name: Optional[str]
    phone: Optional[str]
    is_active: bool
    is_verified: bool
    created_at: datetime
    updated_at: datetime


class UserListResponse(BaseModel):
    """Schema for user list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    email: str
    role: str
    first_name: str
    last_name: str
    is_active: bool
    created_at: datetime
