"""
Pydantic schemas for Homework system with AI integration.

Includes schemas for:
- Homework assignments (teacher-created)
- Tasks (linked to paragraphs)
- Questions (AI-generated or manual)
- Student submissions and answers
"""
from typing import Optional, List, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field, ConfigDict, field_validator, model_validator


# =============================================================================
# Enums (as string enums for flexibility)
# =============================================================================

class HomeworkStatus(str, Enum):
    """Homework lifecycle status."""
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"
    ARCHIVED = "archived"


class TaskType(str, Enum):
    """Type of homework task."""
    READ = "read"
    QUIZ = "quiz"
    OPEN_QUESTION = "open_question"
    ESSAY = "essay"
    PRACTICE = "practice"
    CODE = "code"


class QuestionType(str, Enum):
    """Type of homework question."""
    SINGLE_CHOICE = "single_choice"
    MULTIPLE_CHOICE = "multiple_choice"
    TRUE_FALSE = "true_false"
    SHORT_ANSWER = "short_answer"
    OPEN_ENDED = "open_ended"
    CODE = "code"


class BloomLevel(str, Enum):
    """Bloom's Taxonomy cognitive levels."""
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class StudentHomeworkStatus(str, Enum):
    """Student homework completion status."""
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    GRADED = "graded"
    RETURNED = "returned"


class SubmissionStatus(str, Enum):
    """Individual task submission status."""
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    SUBMITTED = "submitted"
    NEEDS_REVIEW = "needs_review"  # Requires manual teacher review
    GRADED = "graded"


# =============================================================================
# Nested Schemas for JSON fields
# =============================================================================

class QuestionOption(BaseModel):
    """Option for choice questions."""
    id: str = Field(..., description="Unique option ID (a, b, c, d)")
    text: str = Field(..., min_length=1, description="Option text")
    is_correct: bool = Field(default=False, description="Is this the correct answer")


class RubricCriterion(BaseModel):
    """Single criterion in grading rubric."""
    name: str = Field(..., min_length=1, description="Criterion name")
    weight: float = Field(..., ge=0, le=1, description="Weight (0.0 to 1.0)")
    levels: List[str] = Field(..., min_length=2, description="Level descriptions")
    description: Optional[str] = Field(None, description="Criterion description")


class GradingRubric(BaseModel):
    """Rubric for grading open-ended questions."""
    criteria: List[RubricCriterion] = Field(..., min_length=1)
    max_score: int = Field(..., ge=1, le=100, description="Maximum score")

    @field_validator('criteria')
    @classmethod
    def validate_weights(cls, v: List[RubricCriterion]) -> List[RubricCriterion]:
        total_weight = sum(c.weight for c in v)
        if abs(total_weight - 1.0) > 0.01:
            raise ValueError(f'Criteria weights must sum to 1.0, got {total_weight}')
        return v


class GenerationParams(BaseModel):
    """Parameters for AI question generation."""
    questions_count: int = Field(default=5, ge=1, le=20, description="Number of questions")
    question_types: List[QuestionType] = Field(
        default=[QuestionType.SINGLE_CHOICE],
        description="Types of questions to generate"
    )
    bloom_levels: List[BloomLevel] = Field(
        default=[BloomLevel.UNDERSTAND, BloomLevel.APPLY],
        description="Cognitive levels (Bloom's taxonomy)"
    )
    include_explanation: bool = Field(default=True, description="Include explanations")
    language: str = Field(default="ru", description="Language (ru/kz)")
    difficulty: Optional[str] = Field(None, description="Target difficulty (easy/medium/hard)")


class Attachment(BaseModel):
    """File attachment schema."""
    url: str = Field(..., description="URL of uploaded file")
    name: str = Field(..., description="Original filename")
    type: str = Field(..., description="File type: image/pdf/doc")
    size: int = Field(..., ge=0, description="File size in bytes")


# =============================================================================
# Create Schemas
# =============================================================================

class HomeworkCreate(BaseModel):
    """Schema for creating a new homework assignment."""

    title: str = Field(..., min_length=3, max_length=200, description="Homework title")
    description: Optional[str] = Field(None, description="Homework description")
    class_id: int = Field(..., description="Class ID to assign homework to")
    due_date: datetime = Field(..., description="Due date and time")

    # AI settings
    ai_generation_enabled: bool = Field(default=False, description="Enable AI question generation")
    ai_check_enabled: bool = Field(default=False, description="Enable AI answer checking")
    target_difficulty: str = Field(default="auto", description="Target difficulty (easy/medium/hard/auto)")
    personalization_enabled: bool = Field(default=False, description="Enable personalization by mastery")

    # Grading settings
    auto_check_enabled: bool = Field(default=True, description="Auto-check closed questions")
    show_answers_after: str = Field(default="submission", description="When to show answers")
    show_explanations: bool = Field(default=True, description="Show explanations after answer")

    # Late submission policy
    late_submission_allowed: bool = Field(default=False, description="Allow late submissions")
    late_penalty_per_day: int = Field(default=0, ge=0, le=100, description="Penalty % per day")
    grace_period_hours: int = Field(default=0, ge=0, le=168, description="Grace period in hours")
    max_late_days: int = Field(default=7, ge=0, le=30, description="Max days for late submission")

    # Attachments
    attachments: Optional[List[Attachment]] = Field(None, description="Attached files")

    @field_validator('target_difficulty')
    @classmethod
    def validate_difficulty(cls, v: str) -> str:
        allowed = ['easy', 'medium', 'hard', 'auto']
        if v not in allowed:
            raise ValueError(f'target_difficulty must be one of {allowed}')
        return v


class HomeworkUpdate(BaseModel):
    """Schema for updating homework assignment."""

    title: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = None
    due_date: Optional[datetime] = None

    # AI settings
    ai_generation_enabled: Optional[bool] = None
    ai_check_enabled: Optional[bool] = None
    target_difficulty: Optional[str] = None
    personalization_enabled: Optional[bool] = None

    # Grading settings
    auto_check_enabled: Optional[bool] = None
    show_answers_after: Optional[str] = None
    show_explanations: Optional[bool] = None

    # Late policy
    late_submission_allowed: Optional[bool] = None
    late_penalty_per_day: Optional[int] = Field(None, ge=0, le=100)
    grace_period_hours: Optional[int] = Field(None, ge=0, le=168)
    max_late_days: Optional[int] = Field(None, ge=0, le=30)

    # Attachments
    attachments: Optional[List[Attachment]] = Field(None, description="Attached files")


class HomeworkTaskCreate(BaseModel):
    """Schema for creating a task within homework."""

    paragraph_id: Optional[int] = Field(None, description="Paragraph ID (for content-based tasks)")
    chapter_id: Optional[int] = Field(None, description="Chapter ID (alternative to paragraph)")
    task_type: TaskType = Field(..., description="Type of task")
    sort_order: int = Field(default=0, ge=0, description="Order in homework")
    is_required: bool = Field(default=True, description="Is task required")
    points: int = Field(default=10, ge=1, le=100, description="Total points for task")
    time_limit_minutes: Optional[int] = Field(None, ge=1, description="Time limit in minutes")
    max_attempts: int = Field(default=1, ge=1, le=10, description="Max attempts allowed")
    instructions: Optional[str] = Field(None, description="Task instructions")

    # AI generation
    ai_prompt_template: Optional[str] = Field(None, description="Custom AI prompt template")
    generation_params: Optional[GenerationParams] = Field(None, description="AI generation parameters")

    # Attachments
    attachments: Optional[List[Attachment]] = Field(None, description="Attached files for task")

    @model_validator(mode='after')
    def validate_content_link(self):
        if not self.paragraph_id and not self.chapter_id:
            if self.task_type not in [TaskType.PRACTICE, TaskType.CODE]:
                raise ValueError(
                    'Необходимо выбрать параграф или главу для этого типа задания'
                )
        return self


class HomeworkTaskUpdate(BaseModel):
    """Schema for updating a task."""

    task_type: Optional[TaskType] = None
    sort_order: Optional[int] = Field(None, ge=0)
    is_required: Optional[bool] = None
    points: Optional[int] = Field(None, ge=1, le=100)
    time_limit_minutes: Optional[int] = Field(None, ge=1)
    max_attempts: Optional[int] = Field(None, ge=1, le=10)
    instructions: Optional[str] = None
    ai_prompt_template: Optional[str] = None
    generation_params: Optional[GenerationParams] = None
    attachments: Optional[List[Attachment]] = Field(None, description="Attached files for task")


class QuestionCreate(BaseModel):
    """Schema for creating a question."""

    question_text: str = Field(..., min_length=10, description="Question text")
    question_type: QuestionType = Field(..., description="Question type")
    options: Optional[List[QuestionOption]] = Field(None, description="Options for choice questions")
    correct_answer: Optional[str] = Field(None, description="Correct answer for short_answer")
    answer_pattern: Optional[str] = Field(None, description="Regex pattern for validation")
    points: int = Field(default=1, ge=1, le=100, description="Points for correct answer")
    difficulty: Optional[str] = Field(None, description="Difficulty level")
    bloom_level: Optional[BloomLevel] = Field(None, description="Bloom's taxonomy level")
    explanation: Optional[str] = Field(None, description="Explanation shown after answer")

    # AI grading (for open-ended)
    grading_rubric: Optional[GradingRubric] = Field(None, description="Grading rubric")
    expected_answer_hints: Optional[str] = Field(None, description="Hints for AI grading")
    ai_grading_prompt: Optional[str] = Field(None, description="Custom AI grading prompt")

    @model_validator(mode='after')
    def validate_options(self):
        if self.question_type in [QuestionType.SINGLE_CHOICE, QuestionType.MULTIPLE_CHOICE]:
            if not self.options or len(self.options) < 2:
                raise ValueError('Choice questions require at least 2 options')
            correct_count = sum(1 for o in self.options if o.is_correct)
            if correct_count == 0:
                raise ValueError('At least one option must be correct')
            if self.question_type == QuestionType.SINGLE_CHOICE and correct_count > 1:
                raise ValueError('Single choice questions must have exactly one correct option')

        if self.question_type == QuestionType.TRUE_FALSE:
            if not self.options or len(self.options) != 2:
                raise ValueError('True/False questions must have exactly 2 options')

        if self.question_type == QuestionType.SHORT_ANSWER:
            if not self.correct_answer:
                raise ValueError('Short answer questions require correct_answer')

        if self.question_type == QuestionType.OPEN_ENDED:
            if not self.grading_rubric and not self.expected_answer_hints:
                raise ValueError('Open-ended questions require grading_rubric or expected_answer_hints')

        return self


class QuestionUpdate(BaseModel):
    """Schema for updating a question (creates new version)."""

    question_text: Optional[str] = Field(None, min_length=10)
    question_type: Optional[QuestionType] = None
    options: Optional[List[QuestionOption]] = None
    correct_answer: Optional[str] = None
    points: Optional[int] = Field(None, ge=1, le=100)
    difficulty: Optional[str] = None
    bloom_level: Optional[BloomLevel] = None
    explanation: Optional[str] = None
    grading_rubric: Optional[GradingRubric] = None
    expected_answer_hints: Optional[str] = None


# =============================================================================
# Response Schemas
# =============================================================================

class QuestionResponse(BaseModel):
    """Response schema for a question."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[QuestionOption]] = None
    points: int
    difficulty: Optional[str] = None
    bloom_level: Optional[BloomLevel] = None
    explanation: Optional[str] = None
    version: int
    is_active: bool
    ai_generated: bool
    created_at: datetime


class QuestionResponseWithAnswer(QuestionResponse):
    """Question with correct answer (for teacher view)."""
    correct_answer: Optional[str] = None
    grading_rubric: Optional[dict] = None
    expected_answer_hints: Optional[str] = None


class HomeworkTaskResponse(BaseModel):
    """Response schema for a homework task."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: Optional[int] = None
    chapter_id: Optional[int] = None
    paragraph_title: Optional[str] = None
    chapter_title: Optional[str] = None
    task_type: TaskType
    sort_order: int
    is_required: bool
    points: int
    time_limit_minutes: Optional[int] = None
    max_attempts: int
    ai_generated: bool
    instructions: Optional[str] = None
    attachments: Optional[List[Attachment]] = None
    questions_count: int = 0
    questions: List[QuestionResponse] = []


class HomeworkResponse(BaseModel):
    """Response schema for homework assignment."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    status: HomeworkStatus
    due_date: datetime
    class_id: int
    class_name: Optional[str] = None
    teacher_id: int
    teacher_name: Optional[str] = None

    # AI settings
    ai_generation_enabled: bool
    ai_check_enabled: bool
    target_difficulty: str
    personalization_enabled: bool

    # Grading settings
    auto_check_enabled: bool
    show_answers_after: str
    show_explanations: bool

    # Late policy
    late_submission_allowed: bool
    late_penalty_per_day: int
    grace_period_hours: int
    max_late_days: int

    # Attachments
    attachments: Optional[List[Attachment]] = None

    # Computed stats
    total_students: int = 0
    submitted_count: int = 0
    graded_count: int = 0
    average_score: Optional[float] = None

    tasks: List[HomeworkTaskResponse] = []

    created_at: datetime
    updated_at: datetime


class HomeworkListResponse(BaseModel):
    """Lightweight homework list item."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    status: HomeworkStatus
    due_date: datetime
    class_id: int
    class_name: Optional[str] = None
    tasks_count: int = 0
    total_students: int = 0
    submitted_count: int = 0
    ai_generation_enabled: bool
    created_at: datetime


# =============================================================================
# Student-facing Schemas
# =============================================================================

class StudentHomeworkResponse(BaseModel):
    """Homework as seen by student."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    due_date: datetime
    is_overdue: bool = False
    can_submit: bool = True  # False if past max_late_days

    # My progress
    my_status: StudentHomeworkStatus
    my_score: Optional[float] = None
    max_score: float
    my_percentage: Optional[float] = None

    # Late info
    is_late: bool = False
    late_penalty: float = 0

    # Settings
    show_explanations: bool

    # Attachments (materials from teacher)
    attachments: Optional[List[Attachment]] = None

    tasks: List["StudentTaskResponse"] = []


class StudentTaskResponse(BaseModel):
    """Task as seen by student."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    paragraph_id: Optional[int] = None
    paragraph_title: Optional[str] = None
    task_type: TaskType
    instructions: Optional[str] = None
    points: int
    time_limit_minutes: Optional[int] = None

    # Attachments (materials from teacher)
    attachments: Optional[List[Attachment]] = None

    # My progress
    status: SubmissionStatus
    current_attempt: int = 0
    max_attempts: int
    attempts_remaining: int
    submission_id: Optional[int] = None  # ID of current/latest submission

    # Results
    my_score: Optional[float] = None
    questions_count: int = 0
    answered_count: int = 0


class StudentQuestionResponse(BaseModel):
    """Question as seen by student (without correct answer)."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_text: str
    question_type: QuestionType
    options: Optional[List[QuestionOption]] = None  # Without is_correct for student
    points: int

    # My answer (if answered)
    my_answer: Optional[str] = None
    my_selected_options: Optional[List[str]] = None
    is_answered: bool = False


class StudentQuestionWithFeedback(StudentQuestionResponse):
    """Question with feedback after submission."""

    is_correct: Optional[bool] = None
    score: Optional[float] = None
    max_score: float
    explanation: Optional[str] = None

    # AI feedback (for open-ended)
    ai_feedback: Optional[str] = None
    ai_confidence: Optional[float] = None


# =============================================================================
# Submission Schemas
# =============================================================================

class AnswerSubmit(BaseModel):
    """Schema for submitting an answer."""

    question_id: int = Field(..., description="Question ID")
    answer_text: Optional[str] = Field(None, description="Text answer")
    selected_options: Optional[List[str]] = Field(None, description="Selected option IDs")

    @model_validator(mode='after')
    def validate_answer(self):
        if not self.answer_text and not self.selected_options:
            raise ValueError('Either answer_text or selected_options is required')
        return self


class TaskSubmitRequest(BaseModel):
    """Schema for submitting all answers for a task."""

    answers: List[AnswerSubmit] = Field(..., min_length=1, description="List of answers")


class SubmissionResult(BaseModel):
    """Result of answer submission."""

    submission_id: int
    question_id: int
    is_correct: Optional[bool] = None  # None for open-ended until graded
    score: float
    max_score: float

    # Feedback
    feedback: Optional[str] = None
    explanation: Optional[str] = None

    # AI grading (for open-ended)
    ai_feedback: Optional[str] = None
    ai_confidence: Optional[float] = None
    needs_review: bool = False  # True if AI confidence < threshold


class TaskSubmissionResult(BaseModel):
    """Result of task submission."""

    submission_id: int
    task_id: int
    status: SubmissionStatus
    attempt_number: int

    total_score: float
    max_score: float
    percentage: float

    is_late: bool = False
    late_penalty_applied: float = 0
    original_score: Optional[float] = None  # Score before late penalty

    answers: List[SubmissionResult] = []

    # Stats
    correct_count: int = 0
    incorrect_count: int = 0
    needs_review_count: int = 0


# =============================================================================
# Teacher Review Schemas
# =============================================================================

class AnswerForReview(BaseModel):
    """Answer awaiting teacher review."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    question_id: int
    question_text: str
    question_type: QuestionType

    student_id: int
    student_name: str

    answer_text: Optional[str] = None
    submitted_at: datetime

    # AI grading
    ai_score: Optional[float] = None
    ai_confidence: Optional[float] = None
    ai_feedback: Optional[str] = None

    # Grading rubric
    grading_rubric: Optional[dict] = None
    expected_answer_hints: Optional[str] = None


class TeacherReviewRequest(BaseModel):
    """Schema for teacher review of an answer."""

    score: float = Field(..., ge=0, le=100, description="Score (0-100)")
    feedback: Optional[str] = Field(None, description="Teacher feedback")


class TeacherReviewResponse(BaseModel):
    """Response after teacher review."""

    answer_id: int
    teacher_score: float
    teacher_feedback: Optional[str] = None
    reviewed_at: datetime


# =============================================================================
# Analytics Schemas
# =============================================================================

class HomeworkAnalytics(BaseModel):
    """Analytics for a homework assignment."""

    homework_id: int
    title: str

    # Completion stats
    total_students: int
    submitted_count: int
    graded_count: int
    completion_rate: float

    # Score stats
    average_score: Optional[float] = None
    min_score: Optional[float] = None
    max_score: Optional[float] = None
    median_score: Optional[float] = None

    # Time stats
    average_time_seconds: Optional[int] = None

    # Late stats
    late_submissions: int = 0
    on_time_submissions: int = 0

    # Question analytics
    questions_by_difficulty: dict = {}
    most_missed_questions: List[dict] = []

    # AI stats
    ai_graded_count: int = 0
    needs_review_count: int = 0


# Update forward references
StudentHomeworkResponse.model_rebuild()
