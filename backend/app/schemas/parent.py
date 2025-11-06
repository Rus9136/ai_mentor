"""
Pydantic schemas for Parent management.
"""

from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict

from app.schemas.user import UserResponseSchema


class ParentCreate(BaseModel):
    """Schema for creating a new parent (includes user data)."""

    # User fields
    email: EmailStr = Field(..., description="Parent email address")
    password: str = Field(..., min_length=8, description="Parent password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")

    # Children (student IDs to link)
    student_ids: Optional[List[int]] = Field(
        default=[],
        description="List of student IDs to link as children",
    )


class ParentUpdate(BaseModel):
    """Schema for updating an existing parent."""

    # Only specific fields can be updated
    # User fields are updated via UserUpdate schema
    # Children are managed via separate endpoints
    pass


class AddChildrenRequest(BaseModel):
    """Schema for adding children to parent."""

    student_ids: List[int] = Field(..., description="List of student IDs to add as children")


class StudentBriefResponse(BaseModel):
    """Brief schema for student info (for nested use in Parent response)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_code: str
    grade_level: int

    # Nested user data (very brief)
    user: UserResponseSchema


class ParentResponse(BaseModel):
    """Schema for parent response (detailed with user data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    # Nested user data
    user: UserResponseSchema

    # Nested children data (optional, loaded when needed)
    children: Optional[List[StudentBriefResponse]] = None


class ParentListResponse(BaseModel):
    """Schema for parent list response (brief)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime

    # Nested user data (brief)
    user: UserResponseSchema

    # Count of children
    children_count: Optional[int] = 0
