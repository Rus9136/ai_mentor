"""
Paragraph models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from pgvector.sqlalchemy import Vector

from app.models.base import SoftDeleteModel


class Paragraph(SoftDeleteModel):
    """Paragraph model."""

    __tablename__ = "paragraphs"

    # Relationships
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=False, index=True)

    # Paragraph info
    title = Column(String(255), nullable=True)
    number = Column(Integer, nullable=False)  # Paragraph number in chapter
    order = Column(Integer, nullable=False)  # Order in chapter
    content = Column(Text, nullable=False)  # Full text content
    summary = Column(Text, nullable=True)  # Brief summary
    learning_objective = Column(Text, nullable=True)  # Learning objective for the paragraph
    lesson_objective = Column(Text, nullable=True)  # Lesson objective for the paragraph
    key_terms = Column(JSON, nullable=True)  # Array of key terms (e.g., ["term1", "term2"])
    questions = Column(JSON, nullable=True)  # Array of questions (e.g., [{"order": 1, "text": "..."}])

    # Relationships
    chapter = relationship("Chapter", back_populates="paragraphs")
    embeddings = relationship("ParagraphEmbedding", back_populates="paragraph", cascade="all, delete-orphan")
    tests = relationship("Test", back_populates="paragraph", cascade="all, delete-orphan")
    student_progress = relationship("StudentParagraph", back_populates="paragraph", cascade="all, delete-orphan")
    outcome_links = relationship("ParagraphOutcome", back_populates="paragraph", cascade="all, delete-orphan")
    contents = relationship("ParagraphContent", back_populates="paragraph", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Paragraph(id={self.id}, number={self.number}, title='{self.title}')>"


class ParagraphEmbedding(SoftDeleteModel):
    """Paragraph embedding model for RAG."""

    __tablename__ = "paragraph_embeddings"

    # Relationships
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Embedding info
    chunk_index = Column(Integer, nullable=False)  # Index of chunk in paragraph
    chunk_text = Column(Text, nullable=False)  # The chunked text
    embedding = Column(Vector(1536), nullable=False)  # OpenAI embedding dimension
    model = Column(String(100), nullable=False, default="text-embedding-3-small")

    # Relationships
    paragraph = relationship("Paragraph", back_populates="embeddings")

    def __repr__(self) -> str:
        return f"<ParagraphEmbedding(id={self.id}, paragraph_id={self.paragraph_id}, chunk={self.chunk_index})>"
