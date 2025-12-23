"""
Subject model.
"""
from sqlalchemy import Column, String, Integer, Boolean, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Subject(BaseModel):
    """Subject (предмет) model."""

    __tablename__ = "subjects"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name_ru = Column(String(255), nullable=False)
    name_kz = Column(String(255), nullable=False)
    description_ru = Column(Text, nullable=True)
    description_kz = Column(Text, nullable=True)
    grade_from = Column(Integer, default=1, nullable=False)
    grade_to = Column(Integer, default=11, nullable=False)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Relationships
    frameworks = relationship("Framework", back_populates="subject", cascade="all, delete-orphan")
    textbooks = relationship("Textbook", back_populates="subject_rel")
    teachers = relationship("Teacher", back_populates="subject_rel")

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, code='{self.code}', name='{self.name_ru}')>"
