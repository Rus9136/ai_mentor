"""
Pydantic schemas for Student management.
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.user import UserResponseSchema


class StudentCreate(BaseModel):
    """Schema for creating a new student (includes user data)."""

    # User fields
    email: EmailStr = Field(..., description="Student email address")
    password: str = Field(..., min_length=8, description="Student password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")

    # Student fields
    student_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Student code (auto-generated if not provided)",
    )
    grade_level: int = Field(..., ge=1, le=11, description="Grade level (1-11)")
    birth_date: Optional[date] = Field(None, description="Date of birth")


class StudentUpdate(BaseModel):
    """Schema for updating an existing student."""

    # Only student-specific fields can be updated
    # User fields are updated via UserUpdate schema
    student_code: Optional[str] = Field(None, max_length=50, description="Student code")
    grade_level: Optional[int] = Field(None, ge=1, le=11, description="Grade level (1-11)")
    birth_date: Optional[date] = Field(None, description="Date of birth")


class SchoolClassBriefResponse(BaseModel):
    """Brief schema for class info (for nested use in Student response)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    grade_level: int
    academic_year: str


class StudentResponse(BaseModel):
    """Schema for student response (detailed with user data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    user_id: int
    student_code: str
    grade_level: int
    birth_date: Optional[date]
    created_at: datetime
    updated_at: datetime

    # Nested user data
    user: UserResponseSchema

    # Nested classes data (optional, loaded when needed)
    classes: Optional[List[SchoolClassBriefResponse]] = None


class StudentListResponse(BaseModel):
    """Schema for student list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_code: str
    grade_level: int
    created_at: datetime

    # Nested user data (brief)
    user: UserResponseSchema
