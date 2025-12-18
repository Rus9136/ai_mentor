"""
Student models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Date
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class Student(SoftDeleteModel):
    """Student model."""

    __tablename__ = "students"

    # Relationships
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Student info
    student_code = Column(String(50), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False, index=True)  # 1-11
    birth_date = Column(Date, nullable=True)

    # Relationships
    school = relationship("School", back_populates="students")
    user = relationship("User", back_populates="student")
    classes = relationship(
        "SchoolClass",
        secondary="class_students",
        back_populates="students",
    )
    parents = relationship(
        "Parent",
        secondary="parent_students",
        back_populates="children",
    )
    assignments = relationship("StudentAssignment", back_populates="student", cascade="all, delete-orphan")
    test_attempts = relationship("TestAttempt", back_populates="student", cascade="all, delete-orphan")
    mastery_history = relationship("MasteryHistory", back_populates="student", cascade="all, delete-orphan")
    adaptive_groups = relationship("AdaptiveGroup", back_populates="student", cascade="all, delete-orphan")
    paragraph_progress = relationship("StudentParagraph", back_populates="student", cascade="all, delete-orphan")
    learning_sessions = relationship("LearningSession", back_populates="student", cascade="all, delete-orphan")
    embedded_answers = relationship("StudentEmbeddedAnswer", back_populates="student", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Student(id={self.id}, student_code='{self.student_code}', grade={self.grade_level})>"
