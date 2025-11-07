"""
Pydantic schemas for Mastery tracking (A/B/C grouping).

Итерация 8: Схемы для студентов, чтобы получать свой прогресс и A/B/C уровень.
"""

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


class ParagraphMasteryResponse(BaseModel):
    """
    Response schema for paragraph mastery (fine-grained progress).

    Used in:
    - GET /students/mastery/paragraph/{paragraph_id}
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    paragraph_id: int

    # Scores from formative tests
    test_score: Optional[float] = Field(None, description="Latest test score (0.0-1.0)")
    average_score: Optional[float] = Field(None, description="Average score across attempts (0.0-1.0)")
    best_score: Optional[float] = Field(None, description="Best score achieved (0.0-1.0)")
    attempts_count: int = Field(0, description="Number of test attempts")

    # Learning indicators
    time_spent: int = Field(0, description="Time spent in seconds")
    is_completed: bool = Field(False, description="Whether paragraph is marked as completed")
    completed_at: Optional[datetime] = Field(None, description="When paragraph was completed")

    # Status: 'struggling', 'progressing', 'mastered'
    status: str = Field("progressing", description="Mastery status")

    # Timestamps
    last_updated_at: datetime = Field(..., description="Last update timestamp")


class ChapterMasteryResponse(BaseModel):
    """
    Response schema for chapter mastery (A/B/C grouping).

    Used in:
    - GET /students/mastery/chapter/{chapter_id}
    """

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    chapter_id: int

    # Paragraph progress counters
    total_paragraphs: int = Field(0, description="Total paragraphs in chapter")
    completed_paragraphs: int = Field(0, description="Completed paragraphs")
    mastered_paragraphs: int = Field(0, description="Mastered paragraphs (>= 85%)")
    struggling_paragraphs: int = Field(0, description="Struggling paragraphs (< 60%)")

    # Aggregated scores (legacy, may be None)
    average_score: Optional[float] = Field(None, description="Average score across paragraphs")
    weighted_score: Optional[float] = Field(None, description="Weighted score (newer paragraphs weighted higher)")

    # Summative test results
    summative_score: Optional[float] = Field(None, description="Summative test score (0.0-1.0)")
    summative_passed: Optional[bool] = Field(None, description="Whether summative test passed")

    # A/B/C Mastery Level (Iteration 8 algorithm)
    mastery_level: str = Field("C", description="Mastery level (A, B, or C)")
    mastery_score: float = Field(0.0, description="Mastery score (0.0-100.0)")

    # Progress tracking
    progress_percentage: int = Field(0, description="Progress percentage (0-100)")
    estimated_completion_date: Optional[date] = Field(None, description="Estimated completion date")

    # Timestamps
    last_updated_at: datetime = Field(..., description="Last update timestamp")


class ChapterMasteryDetailResponse(BaseModel):
    """
    Detailed response schema for chapter mastery with chapter info.

    Used in:
    - GET /students/mastery/overview (list of chapters)

    Includes chapter title and subject for better UX.
    """

    model_config = ConfigDict(from_attributes=True)

    # Core mastery fields (same as ChapterMasteryResponse)
    id: int
    student_id: int
    chapter_id: int

    # Paragraph progress counters
    total_paragraphs: int = Field(0, description="Total paragraphs in chapter")
    completed_paragraphs: int = Field(0, description="Completed paragraphs")
    mastered_paragraphs: int = Field(0, description="Mastered paragraphs (>= 85%)")
    struggling_paragraphs: int = Field(0, description="Struggling paragraphs (< 60%)")

    # A/B/C Mastery Level
    mastery_level: str = Field("C", description="Mastery level (A, B, or C)")
    mastery_score: float = Field(0.0, description="Mastery score (0.0-100.0)")

    # Progress tracking
    progress_percentage: int = Field(0, description="Progress percentage (0-100)")

    # Summative test results
    summative_score: Optional[float] = Field(None, description="Summative test score (0.0-1.0)")
    summative_passed: Optional[bool] = Field(None, description="Whether summative test passed")

    # Timestamps
    last_updated_at: datetime = Field(..., description="Last update timestamp")

    # Nested chapter info (for display)
    chapter_title: Optional[str] = Field(None, description="Chapter title")
    chapter_order: Optional[int] = Field(None, description="Chapter order in textbook")


class MasteryOverviewResponse(BaseModel):
    """
    Overview response with all chapters for a student.

    Used in:
    - GET /students/mastery/overview
    """

    student_id: int
    chapters: List[ChapterMasteryDetailResponse] = Field(
        default_factory=list,
        description="List of chapter mastery records"
    )
    total_chapters: int = Field(0, description="Total chapters tracked")

    # Aggregated stats
    average_mastery_score: float = Field(0.0, description="Average mastery score across all chapters")
    level_a_count: int = Field(0, description="Number of chapters at level A")
    level_b_count: int = Field(0, description="Number of chapters at level B")
    level_c_count: int = Field(0, description="Number of chapters at level C")
