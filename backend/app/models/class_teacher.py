"""
ClassTeacher association model for many-to-many relationship between classes and teachers.
"""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassTeacher(Base):
    """Association model for class-teacher relationship."""

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

    # Relationships
    school_class = relationship("SchoolClass", back_populates="class_teachers")
    teacher = relationship("Teacher", back_populates="class_teachers")

    __table_args__ = (
        UniqueConstraint("class_id", "teacher_id", name="uq_class_teacher"),
    )

    def __repr__(self) -> str:
        return f"<ClassTeacher(class_id={self.class_id}, teacher_id={self.teacher_id})>"
