"""
Paragraph Prerequisite model for Knowledge Graph.

Tracks dependency relationships between paragraphs within the same textbook.
E.g., "Quadratic equations" requires "Linear equations".
"""

from sqlalchemy import Column, Integer, String, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class ParagraphPrerequisite(BaseModel):
    """Prerequisite link between two paragraphs in the same textbook."""

    __tablename__ = "paragraph_prerequisites"

    paragraph_id = Column(
        Integer,
        ForeignKey("paragraphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    prerequisite_paragraph_id = Column(
        Integer,
        ForeignKey("paragraphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    strength = Column(
        String(10),
        nullable=False,
        default="required",
        server_default="required",
    )

    # Relationships
    paragraph = relationship("Paragraph", foreign_keys=[paragraph_id])
    prerequisite = relationship("Paragraph", foreign_keys=[prerequisite_paragraph_id])

    def __repr__(self) -> str:
        return (
            f"<ParagraphPrerequisite(id={self.id}, "
            f"paragraph_id={self.paragraph_id} ← "
            f"prerequisite_id={self.prerequisite_paragraph_id}, "
            f"strength={self.strength})>"
        )
