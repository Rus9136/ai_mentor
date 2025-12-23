"""
Chat models for RAG-based conversations.
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Text, DateTime, Boolean
from sqlalchemy.orm import relationship
import enum

from app.models.base import SoftDeleteModel


class ChatSessionType(str, enum.Enum):
    """Chat session type enumeration."""

    READING_HELP = "reading_help"       # Помощь при чтении параграфа
    POST_PARAGRAPH = "post_paragraph"   # Обсуждение после прочтения
    TEST_HELP = "test_help"             # Помощь с тестом
    GENERAL_TUTOR = "general_tutor"     # Общий репетитор


class ChatSession(SoftDeleteModel):
    """
    Chat session model - represents a conversation thread.

    Each session belongs to a student and optionally linked to
    a paragraph, chapter, or test for context.
    """

    __tablename__ = "chat_sessions"

    # Relationships (multi-tenant isolation)
    student_id = Column(
        Integer,
        ForeignKey("students.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Session type (stored as String, but uses ChatSessionType enum for validation)
    session_type = Column(
        String(30),
        nullable=False,
        index=True,
        default="general_tutor"
    )

    # Optional context references
    paragraph_id = Column(
        Integer,
        ForeignKey("paragraphs.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    chapter_id = Column(
        Integer,
        ForeignKey("chapters.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    test_id = Column(
        Integer,
        ForeignKey("tests.id", ondelete="SET NULL"),
        nullable=True
    )

    # Session metadata
    title = Column(String(255), nullable=True)
    mastery_level = Column(String(1), nullable=True)  # A, B, or C
    language = Column(String(5), default="ru", nullable=False)

    # Status tracking
    last_message_at = Column(DateTime(timezone=True), nullable=True)
    message_count = Column(Integer, default=0, nullable=False)
    total_tokens_used = Column(Integer, default=0, nullable=False)

    # Relationships
    student = relationship("Student", backref="chat_sessions")
    paragraph = relationship("Paragraph", backref="chat_sessions")
    chapter = relationship("Chapter", backref="chat_sessions")
    test = relationship("Test", backref="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )

    def __repr__(self) -> str:
        return f"<ChatSession(id={self.id}, student={self.student_id}, type='{self.session_type}')>"


class ChatMessage(SoftDeleteModel):
    """
    Chat message model - represents a single message in a conversation.

    Stores both user messages and assistant responses with metadata.
    """

    __tablename__ = "chat_messages"

    # Relationships
    session_id = Column(
        Integer,
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    # Denormalized for RLS efficiency
    school_id = Column(
        Integer,
        ForeignKey("schools.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )

    # Message content
    role = Column(String(20), nullable=False)  # "user" | "assistant" | "system"
    content = Column(Text, nullable=False)

    # RAG metadata (for assistant messages)
    citations_json = Column(Text, nullable=True)  # JSON array of citations
    context_chunks_used = Column(Integer, nullable=True)
    tokens_used = Column(Integer, nullable=True)
    model_used = Column(String(100), nullable=True)
    processing_time_ms = Column(Integer, nullable=True)

    # Relationships
    session = relationship("ChatSession", back_populates="messages")

    def __repr__(self) -> str:
        return f"<ChatMessage(id={self.id}, session={self.session_id}, role='{self.role}')>"
