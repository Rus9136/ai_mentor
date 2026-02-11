"""
Pydantic schemas for embedded questions and self-assessment.
"""
from datetime import datetime
from typing import Optional, List, Literal
from pydantic import BaseModel, ConfigDict, Field


# =============================================================================
# Embedded Question Schemas
# =============================================================================

class QuestionOption(BaseModel):
    """Single option for a question."""
    id: str = Field(..., description="Option identifier (e.g., 'a', 'b', 'c')")
    text: str = Field(..., description="Option text")
    is_correct: bool = Field(default=False, description="Whether this option is correct")


class EmbeddedQuestionBase(BaseModel):
    """Base schema for embedded questions."""
    question_text: str = Field(..., description="The question text")
    question_type: Literal["single_choice", "multiple_choice", "true_false"] = Field(
        default="single_choice",
        description="Type of question"
    )
    options: Optional[List[QuestionOption]] = Field(None, description="Answer options")
    correct_answer: Optional[str] = Field(None, description="Correct answer for true_false type")
    explanation: Optional[str] = Field(None, description="Explanation shown after answering")
    hint: Optional[str] = Field(None, description="Hint shown on request")
    sort_order: int = Field(default=0, description="Order within paragraph")


class EmbeddedQuestionCreate(EmbeddedQuestionBase):
    """Schema for creating an embedded question."""
    paragraph_id: int


class EmbeddedQuestionUpdate(BaseModel):
    """Schema for updating an embedded question (all fields optional)."""
    question_text: Optional[str] = None
    question_type: Optional[Literal["single_choice", "multiple_choice", "true_false"]] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    explanation: Optional[str] = None
    hint: Optional[str] = None
    sort_order: Optional[int] = None


class EmbeddedQuestionResponse(EmbeddedQuestionBase):
    """Schema for embedded question response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    is_active: bool
    created_at: datetime


class EmbeddedQuestionForStudent(BaseModel):
    """
    Schema for embedded question shown to student.
    Does NOT include is_correct in options or correct_answer.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: int
    question_text: str
    question_type: str
    options: Optional[List[dict]] = Field(None, description="Options without is_correct flag")
    hint: Optional[str] = None
    sort_order: int

    @classmethod
    def from_question(cls, question) -> "EmbeddedQuestionForStudent":
        """Create student-safe version of question (without correct answers)."""
        options = None
        if question.options:
            # Remove is_correct from options
            options = [{"id": opt.get("id"), "text": opt.get("text")} for opt in question.options]

        return cls(
            id=question.id,
            paragraph_id=question.paragraph_id,
            question_text=question.question_text,
            question_type=question.question_type,
            options=options,
            hint=question.hint,
            sort_order=question.sort_order
        )


# =============================================================================
# Answer Schemas
# =============================================================================

class AnswerEmbeddedQuestionRequest(BaseModel):
    """Request to answer an embedded question."""
    answer: str | List[str] = Field(..., description="Selected answer(s)")


class AnswerEmbeddedQuestionResponse(BaseModel):
    """Response after answering an embedded question."""
    is_correct: bool
    correct_answer: Optional[str | List[str]] = Field(None, description="The correct answer")
    explanation: Optional[str] = None
    attempts_count: int = 1


class StudentEmbeddedAnswerResponse(BaseModel):
    """Schema for student's embedded answer."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    selected_answer: Optional[str] = None
    selected_options: Optional[List[str]] = None
    is_correct: Optional[bool] = None
    attempts_count: int
    answered_at: datetime


# =============================================================================
# Self-Assessment Schemas
# =============================================================================

class SelfAssessmentRequest(BaseModel):
    """Request to submit self-assessment."""
    rating: Literal["understood", "questions", "difficult"] = Field(
        ...,
        description="Self-assessment rating: understood (всё понятно), questions (есть вопросы), difficult (сложно)"
    )
    practice_score: Optional[float] = Field(
        None, ge=0.0, le=100.0,
        description="Practice score percentage (0-100). Null if no practice"
    )
    time_spent: Optional[int] = Field(
        None, ge=0, le=36000,
        description="Time spent on paragraph in seconds (max 10 hours)"
    )


class SelfAssessmentResponse(BaseModel):
    """Response after submitting self-assessment."""
    id: int
    paragraph_id: int
    rating: str
    practice_score: Optional[float] = None
    mastery_impact: float = Field(..., description="Impact on mastery, corrected by practice_score")
    next_recommendation: str = Field(
        ...,
        description="Recommendation: review, chat_tutor, next_paragraph, or practice_retry"
    )
    created_at: datetime


# =============================================================================
# Step Progress Schemas
# =============================================================================

class UpdateStepRequest(BaseModel):
    """Request to update current step."""
    step: Literal["intro", "content", "practice", "summary", "completed"] = Field(
        ...,
        description="Current learning step"
    )
    time_spent: Optional[int] = Field(
        None,
        ge=0,
        le=3600,
        description="Additional time spent in seconds (0-3600, max 1 hour per update)"
    )


class StepProgressResponse(BaseModel):
    """Response with step progress info."""
    paragraph_id: int
    current_step: str
    is_completed: bool
    time_spent: int
    available_steps: List[str]
    self_assessment: Optional[str] = None


# =============================================================================
# Paragraph Progress Schemas (extended)
# =============================================================================

class ParagraphProgressResponse(BaseModel):
    """Extended paragraph progress with steps and self-assessment."""
    model_config = ConfigDict(from_attributes=True)

    paragraph_id: int
    is_completed: bool
    current_step: Optional[str] = "intro"
    time_spent: int = 0
    last_accessed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    self_assessment: Optional[str] = None
    self_assessment_at: Optional[datetime] = None

    # Available steps based on paragraph content
    available_steps: List[str] = Field(default_factory=lambda: ["intro", "content", "summary"])

    # Embedded questions progress
    embedded_questions_total: int = 0
    embedded_questions_answered: int = 0
    embedded_questions_correct: int = 0
