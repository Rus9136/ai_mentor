"""
Test attempt models.

Note: test_attempts is a partitioned table (RANGE by started_at, monthly).
PRIMARY KEY is (id, started_at) to support PostgreSQL partitioning.
See migration: 5d20a0c758f1_partition_test_attempts.py
"""
from sqlalchemy import Column, Integer, ForeignKey, Float, DateTime, Boolean, Text, String, JSON, PrimaryKeyConstraint
from sqlalchemy.orm import relationship
from datetime import datetime, timezone
import enum

from app.models.base import BaseModel


class AttemptStatus(str, enum.Enum):
    """Test attempt status enumeration.

    Note: The database column is VARCHAR(20), not an enum type.
    This Python enum is used for type safety in application code.
    """

    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    ABANDONED = "abandoned"


class TestAttempt(BaseModel):
    """Test attempt model.

    PARTITIONED TABLE: Uses composite PRIMARY KEY (id, started_at) for partition support.
    Partitions: test_attempts_YYYY_MM (monthly from 2025-01 to 2027-12).
    """

    __tablename__ = "test_attempts"

    # Override BaseModel's id to be part of composite PK
    id = Column(Integer, nullable=False)

    # Partition key - must be part of PRIMARY KEY
    started_at = Column(DateTime(timezone=True), nullable=False, default=lambda: datetime.now(timezone.utc))

    # Composite primary key for partitioning
    __table_args__ = (
        PrimaryKeyConstraint('id', 'started_at'),
        {'postgresql_partition_by': 'RANGE (started_at)'},
    )

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Attempt info
    attempt_number = Column(Integer, nullable=False, default=1)  # Attempt number for this student/test
    status = Column(
        String(20),
        nullable=False,
        default=AttemptStatus.IN_PROGRESS.value,
        index=True
    )
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
