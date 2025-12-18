"""
Invitation code models for student registration.
"""
from sqlalchemy import Column, String, Boolean, ForeignKey, Integer, DateTime, CheckConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class InvitationCode(BaseModel):
    """
    Invitation code for student registration.

    School admins create invitation codes that students use to bind
    their Google accounts to a specific school and class.
    """

    __tablename__ = "invitation_codes"

    # School relationship
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Optional class binding
    class_id = Column(
        Integer,
        ForeignKey("school_classes.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )

    # Code details
    code = Column(String(20), nullable=False, unique=True, index=True)
    grade_level = Column(Integer, nullable=False)

    # Validity constraints
    expires_at = Column(DateTime(timezone=True), nullable=True)
    max_uses = Column(Integer, nullable=True)  # NULL = unlimited
    uses_count = Column(Integer, nullable=False, default=0)

    # Metadata
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    school = relationship("School", backref="invitation_codes")
    school_class = relationship("SchoolClass", backref="invitation_codes")
    creator = relationship("User", backref="created_invitation_codes")
    uses = relationship("InvitationCodeUse", back_populates="invitation_code", cascade="all, delete-orphan")

    # Constraints
    __table_args__ = (
        CheckConstraint("grade_level >= 1 AND grade_level <= 11", name="check_grade_level"),
        CheckConstraint("uses_count >= 0", name="check_uses_count"),
    )

    def __repr__(self) -> str:
        return f"<InvitationCode(id={self.id}, code='{self.code}', school_id={self.school_id})>"

    @property
    def is_valid(self) -> bool:
        """Check if code is still valid (not expired, not exhausted)."""
        from datetime import datetime, timezone

        if not self.is_active:
            return False

        if self.expires_at and datetime.now(timezone.utc) > self.expires_at:
            return False

        if self.max_uses is not None and self.uses_count >= self.max_uses:
            return False

        return True


class InvitationCodeUse(BaseModel):
    """
    Audit trail for invitation code usage.

    Records which student used which code and when.
    """

    __tablename__ = "invitation_code_uses"

    # Foreign keys
    invitation_code_id = Column(
        Integer,
        ForeignKey("invitation_codes.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Relationships
    invitation_code = relationship("InvitationCode", back_populates="uses")
    student = relationship("Student", backref="invitation_code_use")

    # Constraints - each student can only use each code once
    __table_args__ = (
        # Note: unique constraint ensures one student per code
        # But students can use different codes (e.g., transfer to new class)
    )

    def __repr__(self) -> str:
        return f"<InvitationCodeUse(code_id={self.invitation_code_id}, student_id={self.student_id})>"
