"""
Coding challenges models.

Tables for the coding practice module:
- coding_topics: Categories/themes for challenges
- coding_challenges: Individual coding tasks with test cases
- coding_submissions: Student solution attempts
"""
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    ForeignKey,
    Index,
    CheckConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CodingTopic(BaseModel):
    """Category of coding challenges (e.g., Loops, Lists, OOP)."""

    __tablename__ = "coding_topics"

    title = Column(String(200), nullable=False)
    title_kk = Column(String(200), nullable=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    description_kk = Column(Text, nullable=True)
    sort_order = Column(Integer, nullable=False, default=0)
    icon = Column(String(50), nullable=True)
    grade_level = Column(Integer, nullable=True)
    paragraph_id = Column(
        Integer,
        ForeignKey("paragraphs.id", ondelete="SET NULL"),
        nullable=True,
    )
    is_active = Column(Boolean, nullable=False, default=True)

    challenges = relationship(
        "CodingChallenge",
        back_populates="topic",
        order_by="CodingChallenge.sort_order",
    )


class CodingChallenge(BaseModel):
    """A single coding task with test cases for auto-checking."""

    __tablename__ = "coding_challenges"

    topic_id = Column(
        Integer,
        ForeignKey("coding_topics.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    title = Column(String(300), nullable=False)
    title_kk = Column(String(300), nullable=True)
    description = Column(Text, nullable=False)
    description_kk = Column(Text, nullable=True)
    difficulty = Column(String(20), nullable=False, default="easy")
    sort_order = Column(Integer, nullable=False, default=0)
    points = Column(Integer, nullable=False, default=10)
    starter_code = Column(Text, nullable=True)
    solution_code = Column(Text, nullable=True)
    hints = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    hints_kk = Column(JSONB, nullable=False, server_default=text("'[]'::jsonb"))
    test_cases = Column(JSONB, nullable=False)
    time_limit_ms = Column(Integer, nullable=True, default=5000)
    is_active = Column(Boolean, nullable=False, default=True)

    topic = relationship("CodingTopic", back_populates="challenges")
    submissions = relationship("CodingSubmission", back_populates="challenge")

    __table_args__ = (
        Index("idx_coding_challenges_topic_sort", "topic_id", "sort_order"),
        CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_coding_challenge_difficulty",
        ),
        CheckConstraint("points > 0", name="ck_coding_challenge_points"),
    )


class CodingSubmission(BaseModel):
    """A student's attempt at solving a challenge."""

    __tablename__ = "coding_submissions"

    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    challenge_id = Column(
        Integer,
        ForeignKey("coding_challenges.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code = Column(Text, nullable=False)
    status = Column(String(20), nullable=False)
    tests_passed = Column(Integer, nullable=False, default=0)
    tests_total = Column(Integer, nullable=False, default=0)
    execution_time_ms = Column(Integer, nullable=True)
    error_message = Column(Text, nullable=True)
    attempt_number = Column(Integer, nullable=False, default=1)
    xp_earned = Column(Integer, nullable=False, default=0)

    student = relationship("Student")
    challenge = relationship("CodingChallenge", back_populates="submissions")

    __table_args__ = (
        Index("idx_coding_submissions_student_challenge", "student_id", "challenge_id"),
        CheckConstraint(
            "status IN ('passed', 'failed', 'error', 'timeout')",
            name="ck_coding_submission_status",
        ),
    )
