"""
Chapter models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class Chapter(SoftDeleteModel):
    """Chapter model."""

    __tablename__ = "chapters"

    # Relationships
    textbook_id = Column(Integer, ForeignKey("textbooks.id", ondelete="CASCADE"), nullable=False, index=True)

    # Chapter info
    title = Column(String(255), nullable=False)
    number = Column(Integer, nullable=False)  # Chapter number in textbook
    order = Column(Integer, nullable=False)  # Order in textbook
    description = Column(Text, nullable=True)
    learning_objective = Column(Text, nullable=True)  # Learning objective for the chapter

    # Relationships
    textbook = relationship("Textbook", back_populates="chapters")
    paragraphs = relationship("Paragraph", back_populates="chapter", cascade="all, delete-orphan", order_by="Paragraph.order")
    tests = relationship("Test", back_populates="chapter", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Chapter(id={self.id}, number={self.number}, title='{self.title}')>"
