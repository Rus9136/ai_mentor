"""
Pydantic schemas for TestAttempt (student test-taking workflow).
"""
from __future__ import annotations

from typing import Optional, List
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict

from app.models.test_attempt import AttemptStatus
from app.models.test import TestPurpose, DifficultyLevel


# Schema 1: AnswerSubmit - Single answer submission


class AnswerSubmit(BaseModel):
    """Schema for submitting a single answer to a question.

    Note: Both selected_option_ids and answer_text can be empty/None
    to represent an unanswered question (will be scored as incorrect).
    """

    question_id: int = Field(..., description="Question ID")
    selected_option_ids: Optional[List[int]] = Field(
        default=None,
        description="Selected option IDs for SINGLE/MULTIPLE_CHOICE/TRUE_FALSE questions"
    )
    answer_text: Optional[str] = Field(
        default=None,
        description="Text answer for SHORT_ANSWER questions"
    )
    # No validator - empty answers are allowed (scored as incorrect)


# Schema 2: TestAttemptCreate - Starting a test


class TestAttemptCreate(BaseModel):
    """Schema for starting a new test attempt."""

    # NOTE: student_id and school_id are taken from current_user in endpoint
    # NOTE: attempt_number is auto-incremented by the service
    pass  # No fields needed - test_id comes from URL path param


# Schema 3: TestAttemptSubmit - Completing a test (bulk submit)


class TestAttemptSubmit(BaseModel):
    """Schema for completing a test and submitting all answers at once.

    Supports partial submissions - unanswered questions are scored as incorrect.
    """

    answers: List[AnswerSubmit] = Field(
        default_factory=list,
        description="List of answers (can be partial - unanswered questions get score=0)"
    )


# Schema 4: TestAttemptAnswerResponse - Answer with grading results


class TestAttemptAnswerResponse(BaseModel):
    """Schema for a test attempt answer with grading results."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    attempt_id: int
    question_id: int
    selected_option_ids: Optional[List[int]]
    answer_text: Optional[str]
    is_correct: Optional[bool] = Field(
        None,
        description="Whether answer is correct (None before submit, True/False after)"
    )
    points_earned: Optional[float] = Field(
        None,
        description="Points earned for this answer (None before grading)"
    )
    answered_at: datetime
    created_at: datetime
    updated_at: datetime

    # Nested question data - uses QuestionResponseStudent BEFORE submit,
    # QuestionResponse AFTER submit (handled at service layer)
    # NOTE: Import at runtime to avoid circular imports
    question: Optional[dict] = Field(
        None,
        description="Question details (with or without correct answers depending on attempt status)"
    )


# Schema 5: TestAttemptResponse - Basic attempt result


class TestAttemptResponse(BaseModel):
    """Schema for basic test attempt information."""

    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    test_id: int
    school_id: int
    attempt_number: int
    status: AttemptStatus = Field(
        ...,
        description="Attempt status: IN_PROGRESS, COMPLETED, ABANDONED"
    )
    started_at: datetime
    completed_at: Optional[datetime] = Field(
        None,
        description="Completion timestamp (None if status != COMPLETED)"
    )

    # Results (all None if status != COMPLETED)
    score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Final score as decimal (0.0 to 1.0)"
    )
    points_earned: Optional[float] = Field(
        None,
        ge=0.0,
        description="Total points earned"
    )
    total_points: Optional[float] = Field(
        None,
        ge=0.0,
        description="Total points possible"
    )
    passed: Optional[bool] = Field(
        None,
        description="Whether student passed (score >= passing_score)"
    )
    time_spent: Optional[int] = Field(
        None,
        ge=0,
        description="Time spent in seconds"
    )

    created_at: datetime
    updated_at: datetime


# Schema 6: TestAttemptDetailResponse - Detailed attempt with answers


class TestAttemptDetailResponse(TestAttemptResponse):
    """Detailed schema for test attempt including test info and answers."""

    # Nested test data
    test: Optional[dict] = Field(
        None,
        description="Test details (TestResponse)"
    )

    # Nested answers (sorted by question order)
    answers: List[TestAttemptAnswerResponse] = Field(
        default_factory=list,
        description="All answers for this attempt (ordered by question.order)"
    )


# Schema 7: StudentProgressResponse - Student progress summary


class StudentProgressResponse(BaseModel):
    """Schema for student progress summary by chapter/paragraph."""

    # Chapter context
    chapter_id: Optional[int] = Field(None, description="Chapter ID (None for overall progress)")
    chapter_name: Optional[str] = Field(None, description="Chapter name")

    # Paragraph-level progress (from ParagraphMastery)
    total_paragraphs: int = Field(
        default=0,
        ge=0,
        description="Total paragraphs in chapter"
    )
    completed_paragraphs: int = Field(
        default=0,
        ge=0,
        description="Paragraphs marked as completed (is_completed=True)"
    )
    mastered_paragraphs: int = Field(
        default=0,
        ge=0,
        description="Paragraphs with 'mastered' status (>= 85%)"
    )
    struggling_paragraphs: int = Field(
        default=0,
        ge=0,
        description="Paragraphs with 'struggling' status (< 60%)"
    )

    # Aggregated scores
    average_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Average score across completed paragraphs (0.0 to 1.0)"
    )

    # Chapter-level mastery (from ChapterMastery, if exists)
    mastery_level: Optional[str] = Field(
        None,
        description="Mastery level: 'A' (>= 85%), 'B' (60-84%), 'C' (< 60%), or None"
    )
    mastery_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=100.0,
        description="Overall mastery score (0-100)"
    )
    progress_percentage: int = Field(
        default=0,
        ge=0,
        le=100,
        description="Completion progress percentage (0-100)"
    )

    # Test statistics
    tests_attempted: int = Field(default=0, ge=0, description="Total tests started")
    tests_completed: int = Field(default=0, ge=0, description="Total tests completed")
    tests_passed: int = Field(default=0, ge=0, description="Total tests passed")

    # Time tracking
    total_time_spent: int = Field(
        default=0,
        ge=0,
        description="Total time spent on this chapter in seconds"
    )
    last_activity_at: Optional[datetime] = Field(
        None,
        description="Last learning activity timestamp"
    )

    # Paragraph details list
    paragraphs: List[dict] = Field(
        default_factory=list,
        description="List of paragraph mastery records with details"
    )


# Schema 8: AvailableTestResponse - Test available to student


class AvailableTestResponse(BaseModel):
    """Schema for a test available to student with metadata."""

    model_config = ConfigDict(from_attributes=True)

    # Test basic info
    id: int
    school_id: Optional[int] = Field(
        None,
        description="School ID (None for global tests available to all schools)"
    )
    chapter_id: Optional[int]
    paragraph_id: Optional[int]

    title: str
    description: Optional[str]
    test_purpose: TestPurpose = Field(
        ...,
        description="Test purpose: DIAGNOSTIC, FORMATIVE, SUMMATIVE, PRACTICE"
    )
    difficulty: DifficultyLevel
    time_limit: Optional[int] = Field(None, description="Time limit in minutes")
    passing_score: float = Field(..., ge=0.0, le=1.0, description="Passing score (0.0 to 1.0)")
    is_active: bool

    created_at: datetime
    updated_at: datetime

    # Test metadata (calculated)
    question_count: int = Field(
        default=0,
        ge=0,
        description="Number of questions in this test"
    )
    total_points: float = Field(
        default=0.0,
        ge=0.0,
        description="Total points possible (sum of all question points)"
    )

    # Student's history with this test
    attempts_count: int = Field(
        default=0,
        ge=0,
        description="How many times student attempted this test"
    )
    best_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Best score achieved by student (0.0 to 1.0)"
    )
    latest_score: Optional[float] = Field(
        None,
        ge=0.0,
        le=1.0,
        description="Most recent score (0.0 to 1.0)"
    )
    latest_attempt_date: Optional[datetime] = Field(
        None,
        description="Date of most recent attempt"
    )
    can_retake: bool = Field(
        default=True,
        description="Whether student can retake this test (always True for practice, rule-based for others)"
    )
