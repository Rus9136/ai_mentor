"""
School class model.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


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

    # Many-to-many via association objects
    class_students = relationship("ClassStudent", back_populates="school_class", cascade="all, delete-orphan")
    class_teachers = relationship("ClassTeacher", back_populates="school_class", cascade="all, delete-orphan")

    # Convenience relationships via secondary (for backward compatibility)
    students = relationship(
        "Student",
        secondary="class_students",
        back_populates="classes",
        viewonly=True,
    )
    teachers = relationship(
        "Teacher",
        secondary="class_teachers",
        back_populates="classes",
        viewonly=True,
    )
    assignments = relationship("Assignment", back_populates="school_class", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("school_id", "code", name="uq_school_class_code"),
    )

    def __repr__(self) -> str:
        return f"<SchoolClass(id={self.id}, name='{self.name}', grade={self.grade_level})>"
