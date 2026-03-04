"""
Textbook PDF-to-MMD conversion tracking model.
"""
import enum

from sqlalchemy import Column, Integer, String, Text, ForeignKey, Enum, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ConversionStatus(str, enum.Enum):
    """Status of a PDF-to-MMD conversion."""
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class TextbookConversion(BaseModel):
    """Tracks a single PDF-to-MMD conversion for a textbook."""

    __tablename__ = "textbook_conversions"

    textbook_id = Column(
        Integer,
        ForeignKey("textbooks.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    status = Column(
        Enum(ConversionStatus, name="conversion_status", create_type=False),
        nullable=False,
        server_default="PENDING",
    )

    # File paths (relative or absolute)
    pdf_path = Column(String(500), nullable=False)
    mmd_path = Column(String(500), nullable=True)

    # Mathpix tracking
    mathpix_pdf_id = Column(String(255), nullable=True)
    page_count = Column(Integer, nullable=True)

    # Timing
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Error tracking
    error_message = Column(Text, nullable=True)

    # Who initiated
    created_by = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    textbook = relationship("Textbook", lazy="joined")
    creator = relationship("User", foreign_keys=[created_by], lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<TextbookConversion(id={self.id}, textbook_id={self.textbook_id}, "
            f"status={self.status})>"
        )
