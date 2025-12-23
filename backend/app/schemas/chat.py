"""
Pydantic schemas for chat endpoints.
"""
from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.rag import Citation


# =============================================================================
# Chat Session Schemas
# =============================================================================

class ChatSessionCreate(BaseModel):
    """Request to create a new chat session."""
    session_type: str = Field(
        default="general_tutor",
        pattern="^(reading_help|post_paragraph|test_help|general_tutor)$",
        description="Type of chat session"
    )
    paragraph_id: Optional[int] = Field(
        None,
        description="Paragraph context (for reading_help, post_paragraph)"
    )
    chapter_id: Optional[int] = Field(
        None,
        description="Chapter context"
    )
    test_id: Optional[int] = Field(
        None,
        description="Test context (for test_help)"
    )
    title: Optional[str] = Field(
        None,
        max_length=255,
        description="Optional session title"
    )
    language: str = Field(
        default="ru",
        pattern="^(ru|kk)$",
        description="Response language"
    )


class ChatSessionResponse(BaseModel):
    """Response for chat session."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_type: str
    paragraph_id: Optional[int]
    chapter_id: Optional[int]
    test_id: Optional[int]
    title: Optional[str]
    mastery_level: Optional[str]
    language: str
    message_count: int
    total_tokens_used: int
    last_message_at: Optional[datetime]
    created_at: datetime


class ChatSessionListResponse(BaseModel):
    """Response for list of chat sessions."""
    items: List[ChatSessionResponse]
    total: int
    page: int
    page_size: int


class ChatSessionDetailResponse(ChatSessionResponse):
    """Detailed response including messages."""
    messages: List["ChatMessageResponse"] = Field(default_factory=list)


# =============================================================================
# Chat Message Schemas
# =============================================================================

class ChatMessageCreate(BaseModel):
    """Request to send a message."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="User message content"
    )


class ChatMessageResponse(BaseModel):
    """Response for a chat message."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    role: str
    content: str
    citations: Optional[List[Citation]] = Field(default=None)
    tokens_used: Optional[int]
    model_used: Optional[str]
    processing_time_ms: Optional[int]
    created_at: datetime


class ChatResponse(BaseModel):
    """Response after sending a message (includes assistant reply)."""
    user_message: ChatMessageResponse
    assistant_message: ChatMessageResponse
    session: ChatSessionResponse


# =============================================================================
# System Prompt Schemas
# =============================================================================

class SystemPromptCreate(BaseModel):
    """Request to create a system prompt template."""
    prompt_type: str = Field(
        ...,
        pattern="^(reading_help|post_paragraph|test_help|general_tutor)$"
    )
    mastery_level: str = Field(..., pattern="^[ABC]$")
    language: str = Field(default="ru", pattern="^(ru|kk)$")
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    prompt_text: str = Field(..., min_length=10)
    is_active: bool = True


class SystemPromptUpdate(BaseModel):
    """Request to update a system prompt template."""
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    prompt_text: Optional[str] = Field(None, min_length=10)
    is_active: Optional[bool] = None


class SystemPromptResponse(BaseModel):
    """Response for system prompt template."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    prompt_type: str
    mastery_level: str
    language: str
    name: str
    description: Optional[str]
    prompt_text: str
    is_active: bool
    version: int
    created_at: datetime
    updated_at: datetime


# Forward reference resolution
ChatSessionDetailResponse.model_rebuild()
