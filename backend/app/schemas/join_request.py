"""
Schemas for student join requests.
"""
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict


class JoinRequestCreate(BaseModel):
    """Schema for creating a join request (from student side - teacher flow)."""
    invitation_code: str = Field(..., min_length=4, max_length=20)


class StudentJoinRequestCreate(BaseModel):
    """Schema for creating a join request from student profile with FIO."""
    invitation_code: str = Field(..., min_length=4, max_length=20)
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    middle_name: Optional[str] = Field(None, max_length=100)


class JoinRequestResponse(BaseModel):
    """Schema for join request response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    class_id: int
    school_id: int
    status: str
    created_at: datetime
    reviewed_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None


class JoinRequestDetailResponse(BaseModel):
    """Schema for detailed join request (for teacher view)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    created_at: datetime

    # Student info
    student_id: int
    student_code: str
    student_first_name: str
    student_last_name: str
    student_middle_name: Optional[str] = None
    student_email: Optional[str] = None
    student_grade_level: int

    # Class info
    class_id: int
    class_name: str

    # Invitation code info
    invitation_code: Optional[str] = None


class JoinRequestApproveRequest(BaseModel):
    """Schema for approving a request."""
    pass  # No additional data needed


class JoinRequestRejectRequest(BaseModel):
    """Schema for rejecting a request."""
    reason: Optional[str] = Field(None, max_length=500)


class JoinRequestActionResponse(BaseModel):
    """Response after approve/reject action."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    status: str
    reviewed_at: datetime
    message: str


class PendingRequestCountResponse(BaseModel):
    """Count of pending requests for a class."""
    class_id: int
    class_name: str
    pending_count: int


class StudentPendingStatusResponse(BaseModel):
    """Student's pending request status."""
    has_pending_request: bool
    class_name: Optional[str] = None
    class_id: Optional[int] = None
    created_at: Optional[datetime] = None


class StudentJoinRequestStatusResponse(BaseModel):
    """Student's join request status response."""
    model_config = ConfigDict(from_attributes=True)

    id: Optional[int] = None
    status: Optional[str] = None
    class_name: Optional[str] = None
    school_name: Optional[str] = None
    created_at: Optional[datetime] = None
    rejection_reason: Optional[str] = None
    has_request: bool = False
