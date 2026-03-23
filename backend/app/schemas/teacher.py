"""
Pydantic schemas for Teacher management.
"""

import re
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator, model_validator

from app.schemas.user import UserResponseSchema
from app.schemas.goso import SubjectBrief

# Kazakhstan phone format: +7XXXXXXXXXX
_KZ_PHONE_RE = re.compile(r"^\+7\d{10}$")


class TeacherCreate(BaseModel):
    """Schema for creating a new teacher (includes user data)."""

    # User fields — at least one of email/phone must be provided
    email: Optional[EmailStr] = Field(None, description="Teacher email address")
    password: str = Field(..., min_length=8, description="Teacher password (min 8 characters)")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    middle_name: Optional[str] = Field(None, max_length=100, description="Middle name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number (+7XXXXXXXXXX)")

    # Teacher fields
    teacher_code: Optional[str] = Field(
        None,
        max_length=50,
        description="Teacher code (auto-generated if not provided)",
    )
    subject_id: Optional[int] = Field(None, description="Subject ID (legacy, single subject)")
    subject_ids: Optional[List[int]] = Field(None, description="List of subject IDs (multi-subject)")
    bio: Optional[str] = Field(None, description="Teacher biography")

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and v != "":
            if not _KZ_PHONE_RE.match(v):
                raise ValueError("Phone must be in +7XXXXXXXXXX format")
        return v or None

    @model_validator(mode='after')
    def check_email_or_phone(self):
        if not self.email and not self.phone:
            raise ValueError("Either email or phone must be provided")
        return self


class TeacherUpdate(BaseModel):
    """Schema for updating an existing teacher."""

    # Only teacher-specific fields can be updated
    # User fields are updated via UserUpdate schema
    teacher_code: Optional[str] = Field(None, max_length=50, description="Teacher code")
    subject_id: Optional[int] = Field(None, description="Subject ID (legacy, single subject)")
    subject_ids: Optional[List[int]] = Field(None, description="List of subject IDs (multi-subject)")
    bio: Optional[str] = Field(None, description="Teacher biography")


class TeacherResponse(BaseModel):
    """Schema for teacher response (detailed with user data)."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    user_id: int
    teacher_code: str
    subject_id: Optional[int] = Field(None, description="Subject ID (legacy, first subject)")
    subject: Optional[str] = Field(None, description="Subject name (for backward compatibility)")
    subject_rel: Optional[SubjectBrief] = Field(None, description="Subject details (legacy)")
    subject_ids: List[int] = Field(default_factory=list, description="All subject IDs")
    subjects: List[SubjectBrief] = Field(default_factory=list, description="All subjects")
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
    subject_id: Optional[int] = Field(None, description="Subject ID (legacy, first subject)")
    subject: Optional[str] = Field(None, description="Subject name (for backward compatibility)")
    subject_rel: Optional[SubjectBrief] = Field(None, description="Subject details (legacy)")
    subject_ids: List[int] = Field(default_factory=list, description="All subject IDs")
    subjects: List[SubjectBrief] = Field(default_factory=list, description="All subjects")
    created_at: datetime

    # Nested user data (brief)
    user: UserResponseSchema


# Import after class definition to avoid circular import
from app.schemas.student import SchoolClassBriefResponse

TeacherResponse.model_rebuild()
