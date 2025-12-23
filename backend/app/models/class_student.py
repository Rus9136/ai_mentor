"""
ClassStudent association model for many-to-many relationship between classes and students.
"""
from sqlalchemy import Column, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.core.database import Base


class ClassStudent(Base):
    """Association model for class-student relationship."""

    __tablename__ = "class_students"

    id = Column(Integer, primary_key=True, autoincrement=True)
    class_id = Column(
        Integer,
        ForeignKey("school_classes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Relationships
    school_class = relationship("SchoolClass", back_populates="class_students")
    student = relationship("Student", back_populates="class_students")

    __table_args__ = (
        UniqueConstraint("class_id", "student_id", name="uq_class_student"),
    )

    def __repr__(self) -> str:
        return f"<ClassStudent(class_id={self.class_id}, student_id={self.student_id})>"
