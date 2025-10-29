"""
Mastery tracking models.
"""
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Date, String
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class MasteryHistory(BaseModel):
    """Mastery history model for tracking student progress."""

    __tablename__ = "mastery_history"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Mastery info
    mastery_score = Column(Float, nullable=False)  # 0.0 to 1.0
    attempts_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    student = relationship("Student", back_populates="mastery_history")

    def __repr__(self) -> str:
        return f"<MasteryHistory(id={self.id}, student_id={self.student_id}, paragraph_id={self.paragraph_id}, score={self.mastery_score})>"


class AdaptiveGroup(BaseModel):
    """Adaptive group assignment for students (A/B/C grouping)."""

    __tablename__ = "adaptive_groups"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Group info
    group_name = Column(String(10), nullable=False, index=True)  # A, B, or C
    assigned_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    mastery_score = Column(Float, nullable=False)  # Score at time of grouping

    # Relationships
    student = relationship("Student", back_populates="adaptive_groups")

    def __repr__(self) -> str:
        return f"<AdaptiveGroup(id={self.id}, student_id={self.student_id}, paragraph_id={self.paragraph_id}, group='{self.group_name}')>"
