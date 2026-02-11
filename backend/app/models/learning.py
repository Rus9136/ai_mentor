"""
Learning activity models.

Note: learning_activities is a partitioned table (RANGE by activity_timestamp, monthly).
PRIMARY KEY is (id, activity_timestamp) to support PostgreSQL partitioning.
See migration: a6f786ce22f9_partition_learning_activities.py
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Float, Enum as SQLEnum, JSON, Boolean, PrimaryKeyConstraint
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


class SelfAssessmentRating(str, enum.Enum):
    """Self-assessment rating enumeration."""

    UNDERSTOOD = "understood"      # Всё понятно
    QUESTIONS = "questions"        # Есть вопросы
    DIFFICULT = "difficult"        # Сложно


class ParagraphStep(str, enum.Enum):
    """Paragraph learning step enumeration."""

    INTRO = "intro"           # Введение (цель урока, ключевые термины)
    CONTENT = "content"       # Основной контент
    PRACTICE = "practice"     # Встроенные вопросы "Проверь себя"
    SUMMARY = "summary"       # Итог
    COMPLETED = "completed"   # Полностью пройден


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

    # Step tracking (new)
    current_step = Column(String(20), default="intro", nullable=True)

    # Self-assessment (new)
    self_assessment = Column(String(20), nullable=True)
    self_assessment_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="paragraph_progress")
    paragraph = relationship("Paragraph", back_populates="student_progress")

    def __repr__(self) -> str:
        return f"<StudentParagraph(student_id={self.student_id}, paragraph_id={self.paragraph_id}, completed={self.is_completed})>"


class ParagraphSelfAssessment(BaseModel):
    """Append-only self-assessment history per paragraph.

    Each time a student submits a self-assessment on the Summary step,
    a new record is created. Records are never updated or deleted.
    """

    __tablename__ = "paragraph_self_assessments"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Assessment data
    rating = Column(String(20), nullable=False)  # understood / questions / difficult
    mastery_impact = Column(Float, nullable=False, default=0.0)  # +5.0 / 0.0 / -5.0
    practice_score = Column(Float, nullable=True)   # 0.0-100.0, null if no practice
    time_spent = Column(Integer, nullable=True)      # seconds, null if not provided

    # Relationships
    student = relationship("Student")
    paragraph = relationship("Paragraph")

    def __repr__(self) -> str:
        return f"<ParagraphSelfAssessment(student_id={self.student_id}, paragraph_id={self.paragraph_id}, rating={self.rating})>"


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
    """Learning activity model.

    PARTITIONED TABLE: Uses composite PRIMARY KEY (id, activity_timestamp) for partition support.
    Partitions: learning_activities_YYYY_MM (monthly from 2025-01 to 2027-12).
    """

    __tablename__ = "learning_activities"

    # Override BaseModel's id to be part of composite PK
    id = Column(Integer, nullable=False)

    # Partition key - must be part of PRIMARY KEY
    activity_timestamp = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow, index=True)

    # Composite primary key for partitioning
    __table_args__ = (
        PrimaryKeyConstraint('id', 'activity_timestamp'),
        {'postgresql_partition_by': 'RANGE (activity_timestamp)'},
    )

    # Relationships
    session_id = Column(Integer, ForeignKey("learning_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Activity info
    activity_type = Column(SQLEnum(ActivityType), nullable=False, index=True)
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
