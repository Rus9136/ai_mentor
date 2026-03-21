"""
Pydantic schemas for coding AI mentor chat.
"""
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field


class CodingAction(str, Enum):
    """Types of AI mentor actions for coding challenges."""
    HINT = "hint"
    EXPLAIN_ERROR = "explain_error"
    CODE_REVIEW = "code_review"
    STEP_BY_STEP = "step_by_step"
    FREE_CHAT = "free_chat"


class CodingChatStartRequest(BaseModel):
    """Request to start an AI mentor action on a coding challenge."""
    challenge_id: int = Field(..., description="ID of the coding challenge")
    action: CodingAction = Field(..., description="Type of AI action")
    code: str = Field(
        ...,
        max_length=10000,
        description="Current student code"
    )
    error: Optional[str] = Field(
        None,
        max_length=5000,
        description="Error traceback if any"
    )
    test_results: Optional[str] = Field(
        None,
        max_length=5000,
        description="Formatted test results"
    )
    language: str = Field(
        default="ru",
        pattern="^(ru|kk)$",
        description="Response language"
    )


class CodingChatMessageRequest(BaseModel):
    """Request to send a follow-up message in a coding chat session."""
    content: str = Field(
        ...,
        min_length=1,
        max_length=4000,
        description="Follow-up message content"
    )
    code: Optional[str] = Field(
        None,
        max_length=10000,
        description="Updated student code (if changed)"
    )
    error: Optional[str] = Field(
        None,
        max_length=5000,
        description="New error traceback (if re-run)"
    )
