"""
ParagraphContent model for rich content (explanation, audio, slides, video, cards).
"""
from enum import Enum
from sqlalchemy import Column, String, Integer, ForeignKey, Text, UniqueConstraint, CheckConstraint
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ContentStatus(str, Enum):
    """Status of content item."""
    EMPTY = "empty"
    DRAFT = "draft"
    READY = "ready"
    OUTDATED = "outdated"


class ParagraphContent(BaseModel):
    """
    Rich content for a paragraph in a specific language.

    Each paragraph can have multiple ParagraphContent records (one per language: ru, kk).
    Contains: explanation text, media URLs (audio, slides, video), and flashcards.
    """

    __tablename__ = "paragraph_contents"

    # Foreign key to paragraph
    paragraph_id = Column(
        Integer,
        ForeignKey("paragraphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Language (ru or kk)
    language = Column(String(2), nullable=False, default="ru")

    # Main content - explanation text (simplified version of paragraph)
    explain_text = Column(Text, nullable=True)

    # Media URLs (stored in /uploads/paragraph-contents/{paragraph_id}/{language}/)
    audio_url = Column(Text, nullable=True)   # MP3/OGG/WAV
    slides_url = Column(Text, nullable=True)  # PDF/PPTX
    video_url = Column(Text, nullable=True)   # MP4/WEBM

    # Flashcards as JSONB array
    # Format: [{"id": "uuid", "type": "term|fact|check", "front": "...", "back": "...", "order": 1}, ...]
    cards = Column(JSONB, nullable=True)

    # Source tracking - hash of paragraph content to detect when source changed
    source_hash = Column(String(64), nullable=True)

    # Status for each content type
    status_explain = Column(String(20), nullable=False, default="empty")
    status_audio = Column(String(20), nullable=False, default="empty")
    status_slides = Column(String(20), nullable=False, default="empty")
    status_video = Column(String(20), nullable=False, default="empty")
    status_cards = Column(String(20), nullable=False, default="empty")

    # Relationships
    paragraph = relationship("Paragraph", back_populates="contents")

    __table_args__ = (
        UniqueConstraint("paragraph_id", "language", name="uq_paragraph_content_language"),
        CheckConstraint("language IN ('ru', 'kk')", name="chk_paragraph_content_language"),
    )

    def __repr__(self) -> str:
        return f"<ParagraphContent(id={self.id}, paragraph_id={self.paragraph_id}, language='{self.language}')>"
