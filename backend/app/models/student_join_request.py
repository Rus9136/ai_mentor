"""
Student Join Request model for class enrollment approval workflow.

This module provides the model for student requests to join a class,
which requires teacher approval before the student is added.
"""
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, DateTime,
    Enum as SQLEnum, Index, UniqueConstraint
)
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class JoinRequestStatus(str, enum.Enum):
    """Status of student join request."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class StudentJoinRequest(BaseModel):
    """
    Student request to join a class.

    Flow:
    1. Student enters InvitationCode during onboarding
    2. System creates StudentJoinRequest with status=PENDING
    3. Teacher reviews and approves/rejects
    4. On approval: student is added to class via ClassStudent

    Attributes:
        student_id: The student making the request
        class_id: The class they want to join
        school_id: School for isolation (denormalized for RLS)
        invitation_code_id: The code used to make the request
        status: Current status (pending/approved/rejected)
        reviewed_by: User who reviewed the request
        reviewed_at: When the review happened
        rejection_reason: Optional reason for rejection
    """
    __tablename__ = "student_join_requests"

    # Foreign Keys
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    class_id = Column(
        Integer,
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    invitation_code_id = Column(
        Integer,
        ForeignKey("invitation_codes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Status
    status = Column(
        SQLEnum(
            JoinRequestStatus,
            name="join_request_status_enum",
            create_type=True,
            values_callable=lambda obj: [e.value for e in obj]
        ),
        nullable=False,
        default=JoinRequestStatus.PENDING,
        index=True
    )

    # Student FIO (provided during request)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    middle_name = Column(String(100), nullable=True)

    # Review info
    reviewed_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True
    )
    reviewed_at = Column(DateTime(timezone=True), nullable=True)
    rejection_reason = Column(Text, nullable=True)

    # Relationships
    student = relationship("Student", backref="join_requests")
    school_class = relationship("SchoolClass", backref="join_requests")
    school = relationship("School", backref="student_join_requests")
    invitation_code = relationship("InvitationCode", backref="join_requests")
    reviewer = relationship("User", backref="reviewed_join_requests")

    __table_args__ = (
        # Prevent duplicate pending requests for same student-class
        UniqueConstraint(
            "student_id", "class_id",
            name="uq_student_class_join_request"
        ),
        Index("idx_join_request_school_status", "school_id", "status"),
        Index("idx_join_request_class_status", "class_id", "status"),
    )

    def __repr__(self) -> str:
        return (
            f"<StudentJoinRequest(id={self.id}, student_id={self.student_id}, "
            f"class_id={self.class_id}, status={self.status.value})>"
        )
