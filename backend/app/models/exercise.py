"""
Exercise model — structured exercises extracted from textbook paragraphs.

Exercises are parsed from MD files (Жаттығулар sections) and stored
with difficulty levels (A/B/C), sub-exercises as JSONB, and answers
from ЖАУАПТАРЫ sections.
"""
from sqlalchemy import (
    Column, String, Integer, ForeignKey, Text, Boolean,
    UniqueConstraint, Index
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import SoftDeleteModel


class Exercise(SoftDeleteModel):
    """
    Structured exercise from a textbook paragraph.

    Parsed from markdown Жаттығулар sections with A/B/C difficulty levels.
    Sub-exercises (подпункты) stored as JSONB array.
    """
    __tablename__ = "exercises"

    # ---- Relationships ----
    paragraph_id = Column(
        Integer,
        ForeignKey("paragraphs.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=True,
        index=True
    )

    # ---- Exercise info ----
    exercise_number = Column(String(20), nullable=False)  # "19.1", "19.15", "32.4"
    sort_order = Column(Integer, default=0, nullable=False)
    difficulty = Column(String(1), nullable=True)  # 'A', 'B', 'C'

    # ---- Content ----
    content_text = Column(Text, nullable=False)  # markdown/plain text
    content_html = Column(Text, nullable=True)   # HTML with LaTeX for rendering

    # ---- Sub-exercises ----
    # Format: [{"number": "1", "text": "$30°$", "answer": "..."}, ...]
    sub_exercises = Column(JSONB, nullable=True)

    # ---- Answers (from ЖАУАПТАРЫ) ----
    answer_text = Column(Text, nullable=True)
    answer_html = Column(Text, nullable=True)
    has_answer = Column(Boolean, default=False, nullable=False)

    # ---- Metadata ----
    is_starred = Column(Boolean, default=False, nullable=False)  # starred exercises
    language = Column(String(5), default="kk", nullable=False)

    # ---- Relationships ----
    paragraph = relationship("Paragraph", back_populates="exercises")
    school = relationship("School", backref="exercises")

    __table_args__ = (
        UniqueConstraint("paragraph_id", "exercise_number", name="uq_exercise_paragraph_number"),
        Index("idx_exercise_paragraph_difficulty", "paragraph_id", "difficulty"),
        Index("idx_exercise_school", "school_id"),
    )

    def __repr__(self) -> str:
        return f"<Exercise(id={self.id}, number='{self.exercise_number}', difficulty='{self.difficulty}')>"
