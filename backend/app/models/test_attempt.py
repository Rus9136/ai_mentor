"""
Test attempt models.
"""
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Boolean, Text, Enum as SQLEnum, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import BaseModel


class AttemptStatus(str, enum.Enum):
    """Test attempt status enumeration."""

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TestAttempt(BaseModel):
    """Test attempt model."""

    __tablename__ = "test_attempts"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Attempt info
    attempt_number = Column(Integer, nullable=False, default=1)  # Attempt number for this student/test
    status = Column(SQLEnum(AttemptStatus), nullable=False, default=AttemptStatus.IN_PROGRESS, index=True)
    started_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Results
    score = Column(Float, nullable=True)  # 0.0 to 1.0
    points_earned = Column(Float, nullable=True)
    total_points = Column(Float, nullable=True)
    passed = Column(Boolean, nullable=True)
    time_spent = Column(Integer, nullable=True)  # Time spent in seconds

    # Offline sync
    synced_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    student = relationship("Student", back_populates="test_attempts")
    test = relationship("Test", back_populates="attempts")
    answers = relationship("TestAttemptAnswer", back_populates="attempt", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<TestAttempt(id={self.id}, student_id={self.student_id}, test_id={self.test_id}, status='{self.status}')>"


class TestAttemptAnswer(BaseModel):
    """Test attempt answer model."""

    __tablename__ = "test_attempt_answers"

    # Relationships
    attempt_id = Column(Integer, ForeignKey("test_attempts.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Answer info
    selected_option_ids = Column(JSON, nullable=True)  # JSON array of selected option IDs
    answer_text = Column(Text, nullable=True)  # For short answer questions
    is_correct = Column(Boolean, nullable=True)
    points_earned = Column(Float, nullable=True)
    answered_at = Column(DateTime(timezone=True), nullable=False, default=datetime.utcnow)

    # Relationships
    attempt = relationship("TestAttempt", back_populates="answers")
    question = relationship("Question", back_populates="answers")

    def __repr__(self) -> str:
        return f"<TestAttemptAnswer(id={self.id}, attempt_id={self.attempt_id}, question_id={self.question_id})>"
