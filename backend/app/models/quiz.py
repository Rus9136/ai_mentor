"""
Quiz Battle models: quiz sessions, participants, answers, teams.
"""
import enum
from sqlalchemy import Column, String, Integer, Boolean, ForeignKey, DateTime, Enum
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import func

from app.models.base import BaseModel


class QuizSessionStatus(str, enum.Enum):
    LOBBY = "lobby"
    IN_PROGRESS = "in_progress"
    FINISHED = "finished"
    CANCELLED = "cancelled"


class QuizSession(BaseModel):
    """Quiz session — a live quiz game."""

    __tablename__ = "quiz_sessions"

    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False, index=True)
    class_id = Column(Integer, ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True)
    test_id = Column(Integer, ForeignKey("tests.id", ondelete="CASCADE"), nullable=True)  # nullable for quick_question
    join_code = Column(String(6), nullable=False, unique=True)
    status = Column(
        Enum(QuizSessionStatus, values_callable=lambda x: [e.value for e in x], name='quiz_session_status',
             create_type=False),
        nullable=False,
        default=QuizSessionStatus.LOBBY,
        server_default='lobby',
    )
    settings = Column(JSONB, nullable=False, server_default='{}')
    question_count = Column(Integer, nullable=False, default=0)
    current_question_index = Column(Integer, nullable=False, default=-1, server_default='-1')
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    school = relationship("School")
    teacher = relationship("Teacher")
    school_class = relationship("SchoolClass")
    test = relationship("Test")
    participants = relationship("QuizParticipant", back_populates="quiz_session", cascade="all, delete-orphan")
    answers = relationship("QuizAnswer", back_populates="quiz_session", cascade="all, delete-orphan")
    teams = relationship("QuizTeam", back_populates="quiz_session", cascade="all, delete-orphan")

    @property
    def mode(self) -> str:
        return (self.settings or {}).get("mode", "classic")

    def __repr__(self) -> str:
        return f"<QuizSession(id={self.id}, join_code='{self.join_code}', status='{self.status}')>"


class QuizTeam(BaseModel):
    """A team within a quiz session."""

    __tablename__ = "quiz_teams"

    quiz_session_id = Column(Integer, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(50), nullable=False)
    color = Column(String(7), nullable=False)
    total_score = Column(Integer, nullable=False, default=0, server_default='0')
    correct_answers = Column(Integer, nullable=False, default=0, server_default='0')

    # Relationships
    quiz_session = relationship("QuizSession", back_populates="teams")
    participants = relationship("QuizParticipant", back_populates="team")

    def __repr__(self) -> str:
        return f"<QuizTeam(id={self.id}, name='{self.name}', score={self.total_score})>"


class QuizParticipant(BaseModel):
    """A student participating in a quiz session."""

    __tablename__ = "quiz_participants"

    quiz_session_id = Column(Integer, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("quiz_teams.id", ondelete="SET NULL"), nullable=True)
    total_score = Column(Integer, nullable=False, default=0, server_default='0')
    correct_answers = Column(Integer, nullable=False, default=0, server_default='0')
    current_streak = Column(Integer, nullable=False, default=0, server_default='0')
    max_streak = Column(Integer, nullable=False, default=0, server_default='0')
    rank = Column(Integer, nullable=True)
    xp_earned = Column(Integer, nullable=False, default=0, server_default='0')
    joined_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    quiz_session = relationship("QuizSession", back_populates="participants")
    student = relationship("Student")
    school = relationship("School")
    team = relationship("QuizTeam", back_populates="participants")

    def __repr__(self) -> str:
        return f"<QuizParticipant(id={self.id}, student_id={self.student_id}, score={self.total_score})>"


class QuizAnswer(BaseModel):
    """An answer submitted by a participant during a quiz."""

    __tablename__ = "quiz_answers"

    quiz_session_id = Column(Integer, ForeignKey("quiz_sessions.id", ondelete="CASCADE"), nullable=False)
    participant_id = Column(Integer, ForeignKey("quiz_participants.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False, index=True)
    question_index = Column(Integer, nullable=False)
    selected_option = Column(Integer, nullable=False)
    is_correct = Column(Boolean, nullable=False)
    answer_time_ms = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False, default=0, server_default='0')
    answered_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

    # Relationships
    quiz_session = relationship("QuizSession", back_populates="answers")
    participant = relationship("QuizParticipant")
    school = relationship("School")

    def __repr__(self) -> str:
        return f"<QuizAnswer(id={self.id}, participant={self.participant_id}, q={self.question_index})>"
