"""
Test and question models.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Boolean, Enum as SQLEnum, Float
from sqlalchemy.orm import relationship
import enum

from app.models.base import SoftDeleteModel


class DifficultyLevel(str, enum.Enum):
    """Difficulty level enumeration."""

    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class QuestionType(str, enum.Enum):
    """Question type enumeration."""

    SINGLE_CHOICE = "single_choice"  # One correct answer
    MULTIPLE_CHOICE = "multiple_choice"  # Multiple correct answers
    TRUE_FALSE = "true_false"  # True/False question
    SHORT_ANSWER = "short_answer"  # Short text answer


class Test(SoftDeleteModel):
    """Test model."""

    __tablename__ = "tests"

    # Relationships (school_id NULL = global test, NOT NULL = school-specific)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True)
    chapter_id = Column(Integer, ForeignKey("chapters.id", ondelete="CASCADE"), nullable=True, index=True)
    paragraph_id = Column(Integer, ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=True, index=True)

    # Test info
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    difficulty = Column(SQLEnum(DifficultyLevel), nullable=False, default=DifficultyLevel.MEDIUM)
    time_limit = Column(Integer, nullable=True)  # Time limit in minutes
    passing_score = Column(Float, nullable=False, default=0.7)  # 0.0 to 1.0
    is_active = Column(Boolean, default=True, nullable=False)

    # Relationships
    chapter = relationship("Chapter", back_populates="tests")
    paragraph = relationship("Paragraph", back_populates="tests")
    questions = relationship("Question", back_populates="test", cascade="all, delete-orphan", order_by="Question.order")
    attempts = relationship("TestAttempt", back_populates="test", cascade="all, delete-orphan")
    assignment_tests = relationship("AssignmentTest", back_populates="test", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Test(id={self.id}, title='{self.title}', difficulty='{self.difficulty}')>"


class Question(SoftDeleteModel):
    """Question model."""

    __tablename__ = "questions"

    # Relationships
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=False, index=True)

    # Question info
    order = Column(Integer, nullable=False)  # Order in test
    question_type = Column(SQLEnum(QuestionType), nullable=False)
    question_text = Column(Text, nullable=False)
    explanation = Column(Text, nullable=True)  # Explanation of correct answer
    points = Column(Float, nullable=False, default=1.0)  # Points for correct answer

    # Relationships
    test = relationship("Test", back_populates="questions")
    options = relationship("QuestionOption", back_populates="question", cascade="all, delete-orphan", order_by="QuestionOption.order")
    answers = relationship("TestAttemptAnswer", back_populates="question", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, type='{self.question_type}', text='{self.question_text[:50]}...')>"


class QuestionOption(SoftDeleteModel):
    """Question option (answer choice) model."""

    __tablename__ = "question_options"

    # Relationships
    question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"), nullable=False, index=True)

    # Option info
    order = Column(Integer, nullable=False)  # Order in question
    option_text = Column(Text, nullable=False)
    is_correct = Column(Boolean, nullable=False, default=False)

    # Relationships
    question = relationship("Question", back_populates="options")

    def __repr__(self) -> str:
        return f"<QuestionOption(id={self.id}, question_id={self.question_id}, is_correct={self.is_correct})>"
