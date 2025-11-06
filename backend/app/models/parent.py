"""
Parent models and association tables.
"""
from sqlalchemy import Column, Integer, ForeignKey, Table, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel
from app.core.database import Base


# Association table for parent-student many-to-many relationship
parent_students = Table(
    "parent_students",
    Base.metadata,
    Column("id", Integer, primary_key=True, autoincrement=True),
    Column("parent_id", Integer, ForeignKey("parents.id", ondelete="CASCADE"), nullable=False),
    Column("student_id", Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False),
    UniqueConstraint("parent_id", "student_id", name="uq_parent_student"),
)


class Parent(SoftDeleteModel):
    """Parent model."""

    __tablename__ = "parents"

    # Relationships
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # Relationships
    school = relationship("School", back_populates="parents")
    user = relationship("User", back_populates="parent")
    children = relationship(
        "Student",
        secondary="parent_students",
        back_populates="parents",
    )

    def __repr__(self) -> str:
        return f"<Parent(id={self.id}, user_id={self.user_id})>"
