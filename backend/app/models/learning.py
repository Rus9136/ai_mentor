"""
Learning activity models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Float, Enum as SQLEnum, JSON, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class ActivityType(str, enum.Enum):
    """Learning activity type enumeration."""

    READ_PARAGRAPH = "read_paragraph"
    WATCH_VIDEO = "watch_video"
    COMPLETE_TEST = "complete_test"
    ASK_QUESTION = "ask_question"
    VIEW_EXPLANATION = "view_explanation"


class StudentParagraph(BaseModel):
    """Student paragraph progress model."""

    __tablename__ = "student_paragraphs"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Progress
    is_completed = Column(Boolean, default=False, nullable=False)
    time_spent = Column(Integer, nullable=False, default=0)  # Time spent in seconds
    last_accessed_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="paragraph_progress")
    paragraph = relationship("Paragraph", back_populates="student_progress")

    def __repr__(self) -> str:
        return f"<StudentParagraph(student_id={self.student_id}, paragraph_id={self.paragraph_id}, completed={self.is_completed})>"


class LearningSession(BaseModel):
    """Learning session model."""

    __tablename__ = "learning_sessions"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Session info
    session_start = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    session_end = Column(DateTime(timezone=True), nullable=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds

    # Device info (for offline sync)
    device_id = Column(String(255), nullable=True)
    device_type = Column(String(50), nullable=True)  # web, mobile, tablet

    # Relationships
    student = relationship("Student", back_populates="learning_sessions")
    activities = relationship("LearningActivity", back_populates="session", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<LearningSession(id={self.id}, student_id={self.student_id}, start={self.session_start})>"


class LearningActivity(BaseModel):
    """Learning activity model."""

    __tablename__ = "learning_activities"

    # Relationships
    session_id = Column(Integer, ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Activity info
    activity_type = Column(SQLEnum(ActivityType), nullable=False, index=True)
    activity_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)
    duration = Column(Integer, nullable=True)  # Duration in seconds

    # References
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="SET NULL"), nullable=True)

    # Additional data
    activity_metadata = Column(JSON, nullable=True)  # Additional activity metadata

    # Relationships
    session = relationship("LearningSession", back_populates="activities")

    def __repr__(self) -> str:
        return f"<LearningActivity(id={self.id}, type='{self.activity_type}', timestamp={self.activity_timestamp})>"
