"""
Pydantic schemas for Spaced Repetition (Review Schedule).
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class ReviewItemResponse(BaseModel):
    """A single paragraph due for review."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    paragraph_title: Optional[str] = None
    paragraph_number: Optional[str] = None
    chapter_title: Optional[str] = None
    textbook_title: Optional[str] = None

    streak: int = Field(0, description="Leitner level (0-6)")
    next_review_date: date
    last_review_date: Optional[datetime] = None
    total_reviews: int = 0
    successful_reviews: int = 0

    # From paragraph_mastery
    best_score: Optional[float] = None
    effective_score: Optional[float] = None


class DueReviewsResponse(BaseModel):
    """Reviews due for today and upcoming."""

    due_today: List[ReviewItemResponse] = Field(default_factory=list)
    due_today_count: int = 0
    upcoming_week_count: int = 0
    total_active: int = 0


class ReviewResultRequest(BaseModel):
    """Submit result of a review quiz."""

    score: float = Field(..., ge=0.0, le=1.0, description="Review quiz score (0.0-1.0)")


class ReviewResultResponse(BaseModel):
    """Response after submitting a review result."""

    paragraph_id: int
    passed: bool
    score: float
    new_streak: int
    next_review_date: date
    message: str


class ReviewStatsResponse(BaseModel):
    """Overview of student's spaced repetition stats."""

    total_active_reviews: int = 0
    due_today: int = 0
    due_this_week: int = 0
    total_completed_reviews: int = 0
    success_rate: float = 0.0
    average_streak: float = 0.0
