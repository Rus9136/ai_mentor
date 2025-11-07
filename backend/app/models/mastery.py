"""
Mastery tracking models.
"""
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Date, String, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime

from app.models.base import BaseModel


class MasteryHistory(BaseModel):
    """Mastery history model for tracking student progress (polymorphic: paragraph or chapter)."""

    __tablename__ = "mastery_history"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=True, index=True)  # Polymorphic
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True, index=True)  # Polymorphic
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Change tracking (new fields from migration 014)
    previous_score = Column(Float, nullable=True)
    new_score = Column(Float, nullable=True)
    previous_level = Column(String(20), nullable=True)  # For paragraph: status, for chapter: A/B/C
    new_level = Column(String(20), nullable=True)

    # Trigger (what caused this change)
    test_attempt_id = Column(Integer, ForeignKey("test_attempts.id", ondelete="SET NULL"), nullable=True, index=True)

    # Legacy fields (kept for backward compatibility)
    mastery_score = Column(Float, nullable=False)  # 0.0 to 1.0
    attempts_count = Column(Integer, nullable=False, default=0)
    success_rate = Column(Float, nullable=False, default=0.0)  # 0.0 to 1.0
    recorded_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Relationships
    student = relationship("Student", back_populates="mastery_history")

    def __repr__(self) -> str:
        entity = f"paragraph_id={self.paragraph_id}" if self.paragraph_id else f"chapter_id={self.chapter_id}"
        return f"<MasteryHistory(id={self.id}, student_id={self.student_id}, {entity}, score={self.mastery_score})>"


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


class ParagraphMastery(BaseModel):
    """Fine-grained mastery tracking per paragraph (lesson)."""

    __tablename__ = "paragraph_mastery"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Scores from formative tests
    test_score = Column(Float, nullable=True)  # Latest test score
    average_score = Column(Float, nullable=True)  # Average across attempts
    best_score = Column(Float, nullable=True)  # Best score achieved
    attempts_count = Column(Integer, nullable=False, default=0, server_default='0')

    # Learning indicators
    time_spent = Column(Integer, nullable=False, default=0, server_default='0')  # Seconds
    is_completed = Column(Boolean, nullable=False, default=False, server_default='false')
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Status: struggling, progressing, mastered
    status = Column(String(20), nullable=False, default='progressing', server_default='progressing', index=True)

    # Timestamps
    last_updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default='now()')

    def __repr__(self) -> str:
        return f"<ParagraphMastery(id={self.id}, student_id={self.student_id}, paragraph_id={self.paragraph_id}, status='{self.status}')>"


class ChapterMastery(BaseModel):
    """Aggregated mastery tracking per chapter for A/B/C grouping."""

    __tablename__ = "chapter_mastery"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Aggregated from paragraphs
    total_paragraphs = Column(Integer, nullable=False, default=0, server_default='0')
    completed_paragraphs = Column(Integer, nullable=False, default=0, server_default='0')
    mastered_paragraphs = Column(Integer, nullable=False, default=0, server_default='0')  # >= 85%
    struggling_paragraphs = Column(Integer, nullable=False, default=0, server_default='0')  # < 60%

    # Aggregated scores
    average_score = Column(Float, nullable=True)  # Average across paragraphs
    weighted_score = Column(Float, nullable=True)  # Newer paragraphs weighted higher

    # Summative test (final chapter test)
    summative_score = Column(Float, nullable=True)
    summative_passed = Column(Boolean, nullable=True)

    # A/B/C Group
    mastery_level = Column(String(1), nullable=False, default='C', server_default='C', index=True)  # A, B, or C
    mastery_score = Column(Float, nullable=False, default=0.0, server_default='0.0')  # 0-100

    # Progress tracking
    progress_percentage = Column(Integer, nullable=False, default=0, server_default='0')  # 0-100
    estimated_completion_date = Column(Date, nullable=True)

    # Timestamps
    last_updated_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, server_default='now()')

    def __repr__(self) -> str:
        return f"<ChapterMastery(id={self.id}, student_id={self.student_id}, chapter_id={self.chapter_id}, level='{self.mastery_level}')>"
