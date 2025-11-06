"""
Pydantic schemas for Teacher management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.user import UserResponseSchema


class TeacherCreate(BaseModel):
    """Schema for creating a new teacher (includes user data)."""

    # User fields
    email: EmailStr = Field(..., description="Teacher email address")
    password: str = Field(..., min_length=8, description="Teacher password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")

    # Teacher fields
    teacher_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Teacher code (auto-generated if not provided)",
    )
    subject: Optional[str] = Field(None, max_length=100, description="Main subject")
    bio: Optional[str] = Field(None, description="Teacher biography")


class TeacherUpdate(BaseModel):
    """Schema for updating an existing teacher."""

    # Only teacher-specific fields can be updated
    # User fields are updated via UserUpdate schema
    teacher_code: Optional[str] = Field(None, max_length=50, description="Teacher code")
    subject: Optional[str] = Field(None, max_length=100, description="Main subject")
    bio: Optional[str] = Field(None, description="Teacher biography")


class TeacherResponse(BaseModel):
    """Schema for teacher response (detailed with user data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    user_id: int
    teacher_code: str
    subject: Optional[str]
    bio: Optional[str]
    created_at: datetime
    updated_at: datetime

    # Nested user data
    user: UserResponseSchema

    # Nested classes data (optional, loaded when needed)
    classes: Optional[List["SchoolClassBriefResponse"]] = None


class TeacherListResponse(BaseModel):
    """Schema for teacher list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    teacher_code: str
    subject: Optional[str]
    created_at: datetime

    # Nested user data (brief)
    user: UserResponseSchema


# Import after class definition to avoid circular import
from app.schemas.student import SchoolClassBriefResponse

TeacherResponse.model_rebuild()
