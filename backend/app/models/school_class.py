"""
School class models and association tables.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel
from app.core.database import Base


# Association table for class-student many-to-many relationship
class_students = Table(
    "class_students",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("class_id", Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False),
    Column("student_id", Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint("class_id", "student_id", name="uq_class_student"),
)


# Association table for class-teacher many-to-many relationship
class_teachers = Table(
    "class_teachers",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("class_id", Integer, ForeignKey("school_classes.id", ondelete="CASCADE"), nullable=False),
    Column("teacher_id", Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint("class_id", "teacher_id", name="uq_class_teacher"),
)


class SchoolClass(SoftDeleteModel):
    """School class model."""

    __tablename__ = "school_classes"

    # Relationships
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Class info
    name = Column(String(100), nullable=False)
    code = Column(String(50), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False, index=True)  # 1-11
    academic_year = Column(String(20), nullable=False, index=True)  # e.g., "2024-2025"

    # Relationships
    school = relationship("School", back_populates="classes")
    students = relationship(
        "Student",
        secondary="class_students",
        back_populates="classes",
    )
    teachers = relationship(
        "Teacher",
        secondary="class_teachers",
        back_populates="classes",
    )
    assignments = relationship("Assignment", back_populates="school_class", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_class_code"),
    )

    def __repr__(self) -> str:
        return f"<SchoolClass(id={self.id}, name='{self.name}', grade={self.grade_level})>"
