"""
Pydantic schemas for Student content access.

These schemas are used by student-facing endpoints for:
- Textbooks browsing with progress
- Chapters with mastery levels
- Paragraphs with learning status
- Rich content (audio, video, slides, cards)
"""
from typing import Optional, List, Any
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

from app.schemas.goso import SubjectBrief


# =============================================================================
# Textbook Schemas for Students
# =============================================================================

class StudentTextbookProgress(BaseModel):
    """Progress stats for a textbook."""

    chapters_total: int = Field(default=0, description="Total number of chapters")
    chapters_completed: int = Field(default=0, description="Completed chapters count")
    paragraphs_total: int = Field(default=0, description="Total number of paragraphs")
    paragraphs_completed: int = Field(default=0, description="Completed paragraphs count")
    percentage: int = Field(default=0, ge=0, le=100, description="Overall progress percentage")


class StudentTextbookResponse(BaseModel):
    """Textbook response for students with progress."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    subject_id: Optional[int] = Field(None, description="Subject ID (normalized)")
    subject: str = Field(description="Subject name (for backward compatibility)")
    subject_rel: Optional[SubjectBrief] = Field(None, description="Subject details")
    grade_level: int
    description: Optional[str] = None
    is_global: bool = Field(description="True if global textbook, False if school-specific")

    # Progress data
    progress: StudentTextbookProgress
    mastery_level: Optional[str] = Field(None, description="Overall mastery level (A/B/C)")
    last_activity: Optional[datetime] = Field(None, description="Last learning activity timestamp")

    # Optional metadata
    author: Optional[str] = None
    chapters_count: int = Field(default=0, description="Total chapters in textbook")


# =============================================================================
# Chapter Schemas for Students
# =============================================================================

class StudentChapterProgress(BaseModel):
    """Progress stats for a chapter."""

    paragraphs_total: int = Field(default=0)
    paragraphs_completed: int = Field(default=0)
    percentage: int = Field(default=0, ge=0, le=100)


class StudentChapterResponse(BaseModel):
    """Chapter response for students with progress and mastery."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    textbook_id: int
    title: str
    number: int
    order: int
    description: Optional[str] = None
    learning_objective: Optional[str] = None

    # Progress and status
    status: str = Field(
        default="not_started",
        description="Chapter status: completed | in_progress | not_started | locked"
    )
    progress: StudentChapterProgress
    mastery_level: Optional[str] = Field(None, description="Mastery level (A/B/C)")
    mastery_score: Optional[float] = Field(None, description="Mastery score 0-100")

    # Test info
    has_summative_test: bool = Field(default=False, description="Has chapter test")
    summative_passed: Optional[bool] = Field(None, description="Summative test passed")


# =============================================================================
# Paragraph Schemas for Students
# =============================================================================

class StudentParagraphResponse(BaseModel):
    """Paragraph response for students with status."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    title: Optional[str] = None
    number: int
    order: int
    summary: Optional[str] = None

    # Status
    status: str = Field(
        default="not_started",
        description="Paragraph status: completed | in_progress | not_started"
    )

    # Estimated time (calculated from content length or metadata)
    estimated_time: int = Field(default=5, description="Estimated time in minutes")

    # Practice info
    has_practice: bool = Field(default=False, description="Has practice test")
    practice_score: Optional[float] = Field(None, description="Best practice score 0-1")

    # Learning objectives preview
    learning_objective: Optional[str] = None
    key_terms: Optional[List[str]] = None


class StudentParagraphDetailResponse(BaseModel):
    """Full paragraph content for learning."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    chapter_id: int
    title: Optional[str] = None
    number: int
    order: int

    # Full content
    content: str = Field(description="Main paragraph content (HTML/Markdown)")
    summary: Optional[str] = None
    learning_objective: Optional[str] = None
    lesson_objective: Optional[str] = None
    key_terms: Optional[List[str]] = None
    questions: Optional[List[dict]] = None

    # Status
    status: str = Field(default="not_started")
    current_step: Optional[str] = Field(None, description="Current learning step")

    # Rich content availability flags
    has_audio: bool = Field(default=False)
    has_video: bool = Field(default=False)
    has_slides: bool = Field(default=False)
    has_cards: bool = Field(default=False)

    # Chapter context
    chapter_title: Optional[str] = None
    textbook_title: Optional[str] = None


# =============================================================================
# Rich Content Schemas
# =============================================================================

class FlashCard(BaseModel):
    """Single flashcard."""

    id: str
    card_type: str = Field(alias="type", description="Card type: term | fact | check")
    front: str
    back: str
    order: int = 0

    model_config = ConfigDict(populate_by_name=True)


class ParagraphRichContent(BaseModel):
    """Rich content for a paragraph (audio, video, slides, cards)."""

    paragraph_id: int
    language: str = Field(default="ru", description="Content language: ru | kk")

    # Explanation text (simplified version)
    explain_text: Optional[str] = None

    # Media URLs
    audio_url: Optional[str] = None
    video_url: Optional[str] = None
    slides_url: Optional[str] = None

    # Flashcards
    cards: Optional[List[FlashCard]] = None

    # Status flags
    has_explain: bool = Field(default=False)
    has_audio: bool = Field(default=False)
    has_video: bool = Field(default=False)
    has_slides: bool = Field(default=False)
    has_cards: bool = Field(default=False)


# =============================================================================
# Navigation Context
# =============================================================================

class ParagraphNavigationContext(BaseModel):
    """Navigation context for paragraph learning view."""

    # Current position
    current_paragraph_id: int
    current_paragraph_number: int
    current_paragraph_title: Optional[str] = None

    # Chapter info
    chapter_id: int
    chapter_title: str
    chapter_number: int

    # Textbook info
    textbook_id: int
    textbook_title: str

    # Navigation
    previous_paragraph_id: Optional[int] = None
    next_paragraph_id: Optional[int] = None

    # Progress in chapter
    total_paragraphs_in_chapter: int
    current_position_in_chapter: int


# =============================================================================
# Dashboard Summary
# =============================================================================

class ContinueLearningItem(BaseModel):
    """Item for 'Continue Learning' section on dashboard."""

    paragraph_id: int
    paragraph_title: Optional[str] = None
    paragraph_number: int
    chapter_id: int
    chapter_title: str
    textbook_id: int
    textbook_title: str
    subject_id: Optional[int] = Field(None, description="Subject ID (normalized)")
    subject: str = Field(description="Subject name (for backward compatibility)")
    subject_rel: Optional[SubjectBrief] = Field(None, description="Subject details")

    # Progress
    progress_percentage: int = 0
    last_activity: datetime


class StudentDashboardStats(BaseModel):
    """Stats for student dashboard."""

    streak_days: int = Field(default=0, description="Consecutive days of learning")
    total_paragraphs_completed: int = Field(default=0)
    total_tasks_completed: int = Field(default=0)
    total_time_spent_minutes: int = Field(default=0)


class StudentDashboardResponse(BaseModel):
    """Full dashboard data for student."""

    # User info
    student_id: int
    first_name: str
    last_name: Optional[str] = None
    grade_level: int
    school_name: Optional[str] = None

    # Continue learning (last activity)
    continue_learning: Optional[ContinueLearningItem] = None

    # Stats
    stats: StudentDashboardStats

    # Available textbooks (limited list for dashboard)
    textbooks: List[StudentTextbookResponse]
