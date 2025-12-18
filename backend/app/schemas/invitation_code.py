"""
Invitation code schemas.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field


class InvitationCodeCreate(BaseModel):
    """Schema for creating an invitation code."""

    class_id: Optional[int] = Field(None, description="Class ID to bind students to")
    grade_level: int = Field(..., ge=1, le=11, description="Grade level (1-11)")
    expires_at: Optional[datetime] = Field(None, description="Expiration date")
    max_uses: Optional[int] = Field(None, ge=1, description="Maximum number of uses")
    code_prefix: Optional[str] = Field(None, max_length=10, description="Optional prefix for the code")


class InvitationCodeUpdate(BaseModel):
    """Schema for updating an invitation code."""

    class_id: Optional[int] = None
    grade_level: Optional[int] = Field(None, ge=1, le=11)
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = Field(None, ge=1)
    is_active: Optional[bool] = None


class InvitationCodeResponse(BaseModel):
    """Schema for invitation code response."""

    id: int
    code: str
    school_id: int
    class_id: Optional[int] = None
    class_name: Optional[str] = None
    grade_level: int
    expires_at: Optional[datetime] = None
    max_uses: Optional[int] = None
    uses_count: int
    is_active: bool
    created_by: int
    created_by_name: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class InvitationCodeUseResponse(BaseModel):
    """Schema for invitation code use response."""

    id: int
    invitation_code_id: int
    student_id: int
    student_name: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class InvitationCodeListResponse(BaseModel):
    """Schema for paginated invitation code list."""

    items: List[InvitationCodeResponse]
    total: int


class ValidateCodeRequest(BaseModel):
    """Schema for validating an invitation code."""

    code: str = Field(..., min_length=4, max_length=20, description="Invitation code")


class ValidateCodeResponse(BaseModel):
    """Schema for code validation response."""

    valid: bool
    school: Optional[dict] = None  # {"id": 1, "name": "School Name", "code": "school001"}
    school_class: Optional[dict] = None  # {"id": 1, "name": "7-A", "grade_level": 7}
    grade_level: Optional[int] = None
    error: Optional[str] = None  # "code_not_found" | "code_expired" | "code_exhausted"


class OnboardingCompleteRequest(BaseModel):
    """Schema for completing student onboarding."""

    invitation_code: str = Field(..., min_length=4, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)
    birth_date: Optional[datetime] = None


class OnboardingCompleteResponse(BaseModel):
    """Schema for onboarding complete response."""

    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict  # UserResponse dict
    student: dict  # StudentResponse dict
