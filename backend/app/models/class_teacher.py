"""
ClassTeacher association model for many-to-many relationship between classes and teachers.
Supports per-subject assignment and homeroom teacher designation.
"""
from sqlalchemy import Column, Integer, Boolean, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassTeacher(Base):
    """Association model for class-teacher relationship with subject binding."""

    __tablename__ = "class_teachers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(
        Integer,
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    teacher_id = Column(
        Integer,
        ForeignKey("teachers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subject_id = Column(
        Integer,
        ForeignKey("subjects.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    is_homeroom = Column(Boolean, nullable=False, server_default="false")

    # Relationships
    school_class = relationship("SchoolClass", back_populates="class_teachers")
    teacher = relationship("Teacher", back_populates="class_teachers")
    subject = relationship("Subject", lazy="joined")

    __table_args__ = (
        UniqueConstraint("class_id", "teacher_id", "subject_id", name="uq_class_teacher_subject"),
    )

    def __repr__(self) -> str:
        return (
            f"<ClassTeacher(class_id={self.class_id}, teacher_id={self.teacher_id}, "
            f"subject_id={self.subject_id}, is_homeroom={self.is_homeroom})>"
        )
