"""
Pydantic schemas for Presentation generation and CRUD.

Includes slide-level validation models (SlideV2*) used by the service
to sanitize LLM output. These are NOT used in API request/response —
slides_data remains dict (JSONB) for flexibility and backward compat.
"""
import logging
import re
from datetime import datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

logger = logging.getLogger(__name__)


# ═══════════════════════════════════════════════════════════
#  SLIDE VALIDATION MODELS (v2)
#  Used internally to sanitize LLM output before storage.
#  All new fields are Optional with defaults — old JSON
#  (without layout_hint, image_query, etc.) parses fine.
# ═══════════════════════════════════════════════════════════

# Character limits from llm_prompt_v2.md
_LIMIT_TITLE = 60
_LIMIT_SUBTITLE = 90
_LIMIT_BODY = 300
_LIMIT_ITEM = 80
_LIMIT_TERM = 25
_LIMIT_DEFINITION = 90
_LIMIT_QUESTION = 120
_LIMIT_OPTION = 50
_LIMIT_STAT_VALUE = 7
_LIMIT_STAT_LABEL = 35
_LIMIT_IMAGE_QUERY = 60


def _truncate(value: str, limit: int, field_name: str) -> str:
    """Truncate string to limit, log warning if exceeded."""
    if len(value) > limit:
        logger.warning(
            "Slide field '%s' exceeded %d chars (%d), truncating",
            field_name, limit, len(value),
        )
        return value[:limit]
    return value


class SlideTermV2(BaseModel):
    """Single term-definition pair in key_terms slide."""
    term: str = ""
    definition: str = ""

    @model_validator(mode="after")
    def truncate_fields(self):
        self.term = _truncate(self.term, _LIMIT_TERM, "term")
        self.definition = _truncate(self.definition, _LIMIT_DEFINITION, "definition")
        return self


class SlideV2(BaseModel):
    """
    Universal slide model that accepts ALL slide types.
    Unknown fields are ignored. Missing fields get defaults.
    Backward compatible with v1 JSON (no layout_hint, etc.).
    """
    model_config = ConfigDict(extra="ignore")

    type: str = "content"
    title: str = ""
    subtitle: Optional[str] = None
    body: Optional[str] = None
    image_url: Optional[str] = None
    items: Optional[list[str]] = None
    terms: Optional[list[SlideTermV2]] = None
    question: Optional[str] = None
    options: Optional[list[str]] = None
    answer: Optional[int] = None

    # v2 fields — all Optional with backward-compatible defaults
    layout_hint: Optional[Literal["image_left", "image_right", "stat_callout"]] = None
    image_query: Optional[str] = None
    stat_value: Optional[str] = None
    stat_label: Optional[str] = None

    @model_validator(mode="after")
    def sanitize_fields(self):
        """Soft validation: truncate to limits, never raise."""
        self.title = _truncate(self.title, _LIMIT_TITLE, "title")

        if self.subtitle:
            self.subtitle = _truncate(self.subtitle, _LIMIT_SUBTITLE, "subtitle")
        if self.body:
            self.body = _truncate(self.body, _LIMIT_BODY, "body")
        if self.question:
            self.question = _truncate(self.question, _LIMIT_QUESTION, "question")
        if self.stat_label:
            self.stat_label = _truncate(self.stat_label, _LIMIT_STAT_LABEL, "stat_label")

        # stat_value: max 7 chars
        if self.stat_value:
            self.stat_value = _truncate(self.stat_value, _LIMIT_STAT_VALUE, "stat_value")

        # image_query: only latin + spaces + basic punctuation
        if self.image_query:
            self.image_query = _truncate(self.image_query, _LIMIT_IMAGE_QUERY, "image_query")
            cleaned = re.sub(r"[^a-zA-Z0-9 ]", "", self.image_query).strip()
            if cleaned != self.image_query:
                logger.warning(
                    "image_query contained non-latin chars, cleaned: '%s' -> '%s'",
                    self.image_query, cleaned,
                )
                self.image_query = cleaned or None

        # items: truncate each
        if self.items:
            self.items = [_truncate(it, _LIMIT_ITEM, "item") for it in self.items]

        # options: truncate each
        if self.options:
            self.options = [_truncate(op, _LIMIT_OPTION, "option") for op in self.options]

        # Default layout_hint for content slides
        if self.type == "content" and not self.layout_hint:
            if self.stat_value:
                self.layout_hint = "stat_callout"
            else:
                self.layout_hint = "image_left"

        return self


class SlidesDataV2(BaseModel):
    """Top-level validated slides structure."""
    model_config = ConfigDict(extra="ignore")

    title: str = ""
    slides: list[SlideV2] = Field(default_factory=list)
    theme: Optional[str] = None


def validate_slides_data(raw: dict) -> dict:
    """
    Parse and sanitize LLM output through SlideV2 validators.
    Returns plain dict (for JSONB storage). Never raises — returns
    original data on parsing failure with a warning.
    """
    try:
        validated = SlidesDataV2.model_validate(raw)
        return validated.model_dump(exclude_none=True)
    except Exception:
        logger.warning("SlideV2 validation failed, returning raw data", exc_info=True)
        return raw


# ═══════════════════════════════════════════════════════════
#  API REQUEST / RESPONSE SCHEMAS
#  slides_data remains dict for backward compatibility.
# ═══════════════════════════════════════════════════════════


# --- REQUEST ---


class PresentationGenerateRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    slide_count: int = Field(default=10)
    theme: Optional[Literal[
        "warm", "green", "forest", "midnight", "parchment", "slate",
        "electric", "lavender", "coral", "ocean", "sage",
    ]] = None

    @field_validator("slide_count")
    @classmethod
    def validate_slide_count(cls, v: int) -> int:
        if v not in (5, 10, 15):
            raise ValueError("slide_count must be 5, 10, or 15")
        return v


# --- RESPONSE ---


class PresentationContext(BaseModel):
    paragraph_title: str
    chapter_title: str
    textbook_title: str
    subject: str
    grade_level: int
    textbook_id: int
    theme: Optional[str] = None


class PresentationGenerateResponse(BaseModel):
    presentation: dict
    context: PresentationContext


# --- SAVE / CRUD ---


class PresentationSaveRequest(BaseModel):
    paragraph_id: int
    class_id: Optional[int] = None
    language: str = Field(default="kk", pattern="^(kk|ru)$")
    slide_count: int = Field(default=10)
    title: Optional[str] = None
    slides_data: dict
    context_data: dict


class PresentationUpdateRequest(BaseModel):
    title: Optional[str] = None
    slides_data: Optional[dict] = None


class PresentationListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    language: str
    slide_count: int
    paragraph_id: int
    class_id: Optional[int] = None
    subject: Optional[str] = None
    grade_level: Optional[int] = None
    created_at: datetime


class PresentationFullResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    teacher_id: int
    school_id: int
    paragraph_id: int
    class_id: Optional[int] = None
    language: str
    slide_count: int
    slides_data: dict
    context_data: dict
    created_at: datetime
    updated_at: datetime
