"""
Assignment models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean, Enum as SQLEnum, Table, Float
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.models.base import SoftDeleteModel
from app.core.database import Base


class AssignmentStatus(str, enum.Enum):
    """Assignment status enumeration."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    OVERDUE = "overdue"


# Association table for assignment-test many-to-many relationship
assignment_tests = Table(
    "assignment_tests",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("assignment_id", Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False),
    Column("test_id", Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False),
    Column("order", Integer, nullable=False, default=0),  # Order of test in assignment
)


class Assignment(SoftDeleteModel):
    """Assignment model."""

    __tablename__ = "assignments"

    # Relationships
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)

    # Assignment info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    due_date = Column(DateTime(timezone=True), nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    school = relationship("School", back_populates="assignments")
    school_class = relationship("SchoolClass", back_populates="assignments")
    teacher = relationship("Teacher", back_populates="assignments_created")
    tests = relationship("Test", secondary="assignment_tests", back_populates="assignment_tests")
    student_assignments = relationship("StudentAssignment", back_populates="assignment", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Assignment(id={self.id}, title='{self.title}', class_id={self.class_id})>"


class AssignmentTest(SoftDeleteModel):
    """Assignment-Test association model with additional metadata."""

    __tablename__ = "assignment_tests"

    # Relationships
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)

    # Metadata
    order = Column(Integer, nullable=False, default=0)  # Order of test in assignment

    # Relationships
    assignment = relationship("Assignment")
    test = relationship("Test", back_populates="assignment_tests")

    def __repr__(self) -> str:
        return f"<AssignmentTest(assignment_id={self.assignment_id}, test_id={self.test_id})>"


class StudentAssignment(SoftDeleteModel):
    """Student assignment model."""

    __tablename__ = "student_assignments"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    assignment_id = Column(Integer, ForeignKey("assignments.id", ondelete="CASCADE"), nullable=False, index=True)

    # Status
    status = Column(SQLEnum(AssignmentStatus), nullable=False, default=AssignmentStatus.NOT_STARTED, index=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Progress
    progress_percentage = Column(Integer, nullable=False, default=0)  # 0-100
    score = Column(Float, nullable=True)  # Overall score 0.0 to 1.0

    # Relationships
    student = relationship("Student", back_populates="assignments")
    assignment = relationship("Assignment", back_populates="student_assignments")

    def __repr__(self) -> str:
        return f"<StudentAssignment(id={self.id}, student_id={self.student_id}, status='{self.status}')>"
