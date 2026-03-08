"""
LLM Usage Log model for tracking token consumption across all AI features.
"""
import enum

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Float,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class LLMFeature(str, enum.Enum):
    """Features that use LLM."""
    CHAT = "chat"
    RAG = "rag"
    LESSON_PLAN = "lesson_plan"
    HOMEWORK_GENERATION = "homework_generation"
    HOMEWORK_GRADING = "homework_grading"
    AUDIO_TEXT = "audio_text"
    MEMORY = "memory"
    SYSTEM = "system"


class LLMUsageLog(BaseModel):
    """Log entry for LLM API usage and token consumption."""

    __tablename__ = "llm_usage_logs"

    # Who
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="SET NULL"), nullable=True, index=True)
    student_id = Column(Integer, ForeignKey("students.id", ondelete="SET NULL"), nullable=True)
    teacher_id = Column(Integer, ForeignKey("teachers.id", ondelete="SET NULL"), nullable=True)

    # What
    feature = Column(
        Enum(LLMFeature, name="llm_feature", create_type=False, values_callable=lambda x: [e.value for e in x]),
        nullable=False,
        index=True,
    )
    provider = Column(String(50), nullable=False)  # cerebras, openrouter, openai
    model = Column(String(100), nullable=False)

    # Tokens
    prompt_tokens = Column(Integer, nullable=True)
    completion_tokens = Column(Integer, nullable=True)
    total_tokens = Column(Integer, nullable=True)

    # Performance
    latency_ms = Column(Integer, nullable=True)

    # Status
    success = Column(Boolean, default=True, nullable=False)
    error_message = Column(Text, nullable=True)

    # Cost
    estimated_cost_usd = Column(Float, nullable=True)

    __table_args__ = (
        Index("ix_llm_usage_logs_school_created", "school_id", "created_at"),
    )
