"""
Review Schedule model for Spaced Repetition system.

Tracks when each mastered paragraph needs to be reviewed,
using the Leitner system with increasing intervals.
"""

from sqlalchemy import Column, Integer, ForeignKey, DateTime, Date, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class ReviewSchedule(BaseModel):
    """Spaced repetition schedule for a student's paragraph."""

    __tablename__ = "review_schedule"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Leitner system
    streak = Column(Integer, nullable=False, default=0, server_default='0')
    next_review_date = Column(Date, nullable=False, index=True)
    last_review_date = Column(DateTime(timezone=True), nullable=True)

    # Statistics
    total_reviews = Column(Integer, nullable=False, default=0, server_default='0')
    successful_reviews = Column(Integer, nullable=False, default=0, server_default='0')

    # Active only when paragraph is mastered
    is_active = Column(Boolean, nullable=False, default=True, server_default='true')

    # Relationships
    student = relationship("Student")
    paragraph = relationship("Paragraph")

    def __repr__(self) -> str:
        return (
            f"<ReviewSchedule(id={self.id}, student_id={self.student_id}, "
            f"paragraph_id={self.paragraph_id}, streak={self.streak}, "
            f"next_review={self.next_review_date})>"
        )
