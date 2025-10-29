"""
Textbook content models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class Textbook(SoftDeleteModel):
    """Textbook model."""

    __tablename__ = "textbooks"

    # Relationships
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Textbook info
    title = Column(String(255), nullable=False, index=True)
    subject = Column(String(100), nullable=False, index=True)
    grade_level = Column(Integer, nullable=False, index=True)  # 1-11
    author = Column(String(255), nullable=True)
    publisher = Column(String(255), nullable=True)
    year = Column(Integer, nullable=True)
    isbn = Column(String(50), nullable=True)
    description = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    school = relationship("School", back_populates="textbooks")
    chapters = relationship("Chapter", back_populates="textbook", cascade="all, delete-orphan", order_by="Chapter.order")

    def __repr__(self) -> str:
        return f"<Textbook(id={self.id}, title='{self.title}', subject='{self.subject}', grade={self.grade_level})>"
