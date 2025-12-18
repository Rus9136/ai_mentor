"""
Pydantic schemas for ParagraphContent (rich content: explanation, audio, slides, video, cards).
"""
from typing import Optional, List, Literal
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


# Card item schema for flashcards
class CardItem(BaseModel):
    """Schema for a single flashcard."""

    id: str = Field(..., description="Unique card ID (UUID)")
    type: Literal["term", "fact", "check"] = Field(
        ...,
        description="Card type: term (definition), fact (key fact), check (self-check question)"
    )
    front: str = Field(..., min_length=1, description="Front side of the card (question/term)")
    back: str = Field(..., min_length=1, description="Back side of the card (answer/definition)")
    order: int = Field(..., ge=0, description="Display order")


# Content status type
ContentStatusType = Literal["empty", "draft", "ready", "outdated"]


# Create schema
class ParagraphContentCreate(BaseModel):
    """Schema for creating paragraph content."""

    language: Literal["ru", "kk"] = Field(default="ru", description="Content language")
    explain_text: Optional[str] = Field(None, description="Simplified explanation text")


# Update schema
class ParagraphContentUpdate(BaseModel):
    """Schema for updating paragraph content."""

    explain_text: Optional[str] = Field(None, description="Simplified explanation text")
    cards: Optional[List[CardItem]] = Field(None, description="Flashcards array")


# Cards update schema (separate endpoint)
class ParagraphContentCardsUpdate(BaseModel):
    """Schema for updating flashcards."""

    cards: List[CardItem] = Field(..., description="Flashcards array")


# Response schema
class ParagraphContentResponse(BaseModel):
    """Full response schema for paragraph content."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    language: str

    # Content
    explain_text: Optional[str] = None
    audio_url: Optional[str] = None
    slides_url: Optional[str] = None
    video_url: Optional[str] = None
    cards: Optional[List[CardItem]] = None

    # Metadata
    source_hash: Optional[str] = None

    # Statuses
    status_explain: str
    status_audio: str
    status_slides: str
    status_video: str
    status_cards: str

    # Timestamps
    created_at: datetime
    updated_at: datetime


# List response schema (compact)
class ParagraphContentListResponse(BaseModel):
    """Compact response for listing paragraph contents."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    language: str

    # Only statuses for list view
    status_explain: str
    status_audio: str
    status_slides: str
    status_video: str
    status_cards: str

    # Has content flags (computed)
    has_explain: bool = Field(default=False, description="Has explanation text")
    has_audio: bool = Field(default=False, description="Has audio file")
    has_slides: bool = Field(default=False, description="Has slides file")
    has_video: bool = Field(default=False, description="Has video file")
    has_cards: bool = Field(default=False, description="Has flashcards")


# Media upload response
class MediaUploadResponse(BaseModel):
    """Response after media file upload."""

    url: str = Field(..., description="URL to access the uploaded file")
    status: str = Field(..., description="New status (usually 'ready')")


# Summary for paragraph list (shows content availability)
class ParagraphContentSummary(BaseModel):
    """Summary of available content for a paragraph (for list views)."""

    paragraph_id: int
    has_ru: bool = Field(default=False, description="Has Russian content")
    has_kk: bool = Field(default=False, description="Has Kazakh content")

    # Russian content statuses
    ru_status_explain: Optional[str] = None
    ru_status_audio: Optional[str] = None
    ru_status_slides: Optional[str] = None
    ru_status_video: Optional[str] = None
    ru_status_cards: Optional[str] = None

    # Kazakh content statuses
    kk_status_explain: Optional[str] = None
    kk_status_audio: Optional[str] = None
    kk_status_slides: Optional[str] = None
    kk_status_video: Optional[str] = None
    kk_status_cards: Optional[str] = None
