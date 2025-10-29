"""
Teacher models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class Teacher(SoftDeleteModel):
    """Teacher model."""

    __tablename__ = "teachers"

    # Relationships
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Teacher info
    teacher_code = Column(String(50), nullable=False, index=True)
    subject = Column(String(100), nullable=True)  # Main subject
    bio = Column(Text, nullable=True)

    # Relationships
    school = relationship("School", back_populates="teachers")
    user = relationship("User", back_populates="teacher")
    classes = relationship(
        "SchoolClass",
        secondary="class_teachers",
        back_populates="teachers",
    )
    assignments_created = relationship("Assignment", back_populates="teacher", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Teacher(id={self.id}, teacher_code='{self.teacher_code}', subject='{self.subject}')>"
