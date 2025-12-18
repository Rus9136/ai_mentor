"""
Embedded questions models for "Check yourself" questions within paragraphs.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
import enum

from app.models.base import BaseModel


class EmbeddedQuestionType(str, enum.Enum):
    """Embedded question type enumeration."""

    SINGLE_CHOICE = "single_choice"      # Один правильный ответ
    MULTIPLE_CHOICE = "multiple_choice"  # Несколько правильных ответов
    TRUE_FALSE = "true_false"            # Верно/Неверно


class EmbeddedQuestion(BaseModel):
    """
    Embedded question model for "Check yourself" questions within paragraphs.

    These are lightweight questions shown inline during paragraph reading,
    not full tests. Used for active learning engagement.
    """

    __tablename__ = "embedded_questions"

    # Relationship to paragraph
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False, index=True)

    # Question content
    question_text = Column(Text, nullable=False)
    question_type = Column(String(20), nullable=False, default="single_choice")

    # Options in JSONB format:
    # [{"id": "a", "text": "Option A", "is_correct": true}, ...]
    options = Column(JSONB, nullable=True)

    # For simple answers (true_false type)
    correct_answer = Column(String(255), nullable=True)

    # Feedback
    explanation = Column(Text, nullable=True)  # Shown after answering
    hint = Column(Text, nullable=True)         # Shown on request before answering

    # Ordering and status
    sort_order = Column(Integer, nullable=False, default=0)
    is_active = Column(Boolean, nullable=False, default=True)

    # Relationships
    paragraph = relationship("Paragraph", back_populates="embedded_questions")
    student_answers = relationship("StudentEmbeddedAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<EmbeddedQuestion(id={self.id}, paragraph_id={self.paragraph_id}, type='{self.question_type}')>"

    def check_answer(self, answer: str | list) -> bool:
        """
        Check if the given answer is correct.

        Args:
            answer: For single_choice/true_false - string answer id
                   For multiple_choice - list of answer ids

        Returns:
            True if answer is correct, False otherwise
        """
        if self.question_type == "true_false":
            return str(answer).lower() == str(self.correct_answer).lower()

        if self.question_type == "single_choice":
            if not self.options:
                return False
            for opt in self.options:
                if opt.get("id") == answer and opt.get("is_correct"):
                    return True
            return False

        if self.question_type == "multiple_choice":
            if not self.options or not isinstance(answer, list):
                return False
            correct_ids = {opt.get("id") for opt in self.options if opt.get("is_correct")}
            return set(answer) == correct_ids

        return False


class StudentEmbeddedAnswer(BaseModel):
    """
    Student's answer to an embedded question.

    Tracks student responses to embedded questions for analytics
    and progress tracking.
    """

    __tablename__ = "student_embedded_answers"

    # Relationships
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True)
    question_id = Column(Integer, ForeignKey("embedded_questions.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)

    # Answer data
    selected_answer = Column(String(255), nullable=True)  # For single choice / true_false
    selected_options = Column(JSONB, nullable=True)       # For multiple choice: ["a", "c"]

    # Result
    is_correct = Column(Boolean, nullable=True)
    attempts_count = Column(Integer, nullable=False, default=1)

    # Timestamp
    answered_at = Column(DateTime(timezone=True), nullable=False)

    # Relationships
    student = relationship("Student", back_populates="embedded_answers")
    question = relationship("EmbeddedQuestion", back_populates="student_answers")

    def __repr__(self) -> str:
        return f"<StudentEmbeddedAnswer(student_id={self.student_id}, question_id={self.question_id}, correct={self.is_correct})>"
