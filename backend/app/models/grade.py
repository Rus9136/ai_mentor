"""
Grade model for school gradebook (journal).
"""
import enum

from sqlalchemy import Column, Integer, SmallInteger, ForeignKey, String, Text, Date, Boolean, DateTime, Enum
from sqlalchemy.orm import relationship
from sqlalchemy import func

from app.models.base import BaseModel


class GradeType(str, enum.Enum):
    """Types of school grades."""
    CURRENT = "CURRENT"  # Текущая оценка
    SOR = "SOR"          # Суммативное оценивание за раздел
    SOCH = "SOCH"        # Суммативное оценивание за четверть
    EXAM = "EXAM"        # Экзамен


class Grade(BaseModel):
    """School grade (оценка) for the gradebook journal."""

    __tablename__ = "grades"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    subject_id = Column(Integer, ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True, index=True)
    created_by = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Grade data
    grade_value = Column(SmallInteger, nullable=False)  # 1-10
    grade_type = Column(Enum(GradeType, name="grade_type", create_type=False), nullable=False, server_default="CURRENT")
    grade_date = Column(Date, nullable=False)
    quarter = Column(SmallInteger, nullable=False)  # 1-4
    academic_year = Column(String(9), nullable=False)  # "2025-2026"
    comment = Column(Text, nullable=True)

    # Soft delete
    is_deleted = Column(Boolean, nullable=False, default=False, server_default="false")
    deleted_at = Column(DateTime(timezone=True), nullable=True)

    # ORM relationships
    student = relationship("Student", lazy="joined")
    subject = relationship("Subject", lazy="joined")
    school_class = relationship("SchoolClass", lazy="noload")
    teacher = relationship("Teacher", lazy="noload")
    creator = relationship("User", foreign_keys=[created_by], lazy="noload")

    def __repr__(self) -> str:
        return (
            f"<Grade(id={self.id}, student_id={self.student_id}, "
            f"subject_id={self.subject_id}, value={self.grade_value}, "
            f"type={self.grade_type})>"
        )
