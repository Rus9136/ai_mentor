"""
School models.
"""
from sqlalchemy import Column, String, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class School(SoftDeleteModel):
    """School (tenant) model."""

    __tablename__ = "schools"

    name = Column(String(255), nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Contact info
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    address = Column(Text, nullable=True)

    # Relationships
    users = relationship("User", back_populates="school", cascade="all, delete-orphan")
    students = relationship("Student", back_populates="school", cascade="all, delete-orphan")
    teachers = relationship("Teacher", back_populates="school", cascade="all, delete-orphan")
    parents = relationship("Parent", back_populates="school", cascade="all, delete-orphan")
    classes = relationship("SchoolClass", back_populates="school", cascade="all, delete-orphan")
    textbooks = relationship("Textbook", back_populates="school", cascade="all, delete-orphan")
    assignments = relationship("Assignment", back_populates="school", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<School(id={self.id}, name='{self.name}', code='{self.code}')>"
