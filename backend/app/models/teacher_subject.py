"""
TeacherSubject association model for many-to-many relationship between teachers and subjects.
"""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class TeacherSubject(Base):
    """Association model for teacher-subject relationship."""

    __tablename__ = "teacher_subjects"

    id = Column(Integer, primary_key=True, autoincrement=True)
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    teacher = relationship("Teacher", back_populates="teacher_subjects")
    subject = relationship("Subject")

    __table_args__ = (
        UniqueConstraint("teacher_id", "subject_id", name="uq_teacher_subject"),
    )

    def __repr__(self) -> str:
        return f"<TeacherSubject(teacher_id={self.teacher_id}, subject_id={self.subject_id})>"
