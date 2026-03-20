"""
Pydantic schemas for the coding challenges and courses module.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

class TopicResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    title_kk: Optional[str] = None
    slug: str
    description: Optional[str] = None
    description_kk: Optional[str] = None
    sort_order: int
    icon: Optional[str] = None
    grade_level: Optional[int] = None
    is_active: bool


class TopicWithProgress(TopicResponse):
    """Topic enriched with student progress stats."""
    total_challenges: int = 0
    solved_challenges: int = 0


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------

class TestCasePublic(BaseModel):
    """Public view of a test case (hidden tests show only description)."""
    input: str
    expected_output: str
    description: Optional[str] = None
    is_hidden: bool = False


class ChallengeListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    title_kk: Optional[str] = None
    difficulty: str
    points: int
    sort_order: int
    # Student-specific
    status: str = "not_started"  # not_started, attempted, solved


class ChallengeDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    topic_id: int
    title: str
    title_kk: Optional[str] = None
    description: str
    description_kk: Optional[str] = None
    difficulty: str
    points: int
    starter_code: Optional[str] = None
    hints: list = Field(default_factory=list)
    hints_kk: list = Field(default_factory=list)
    test_cases: list[TestCasePublic] = Field(default_factory=list)
    time_limit_ms: Optional[int] = 5000
    # Student-specific
    status: str = "not_started"
    best_submission: Optional["SubmissionResponse"] = None


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

class SubmissionCreate(BaseModel):
    code: str = Field(..., min_length=1, max_length=50000)
    tests_passed: int = Field(..., ge=0)
    tests_total: int = Field(..., ge=1)
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None


class SubmissionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    challenge_id: int
    code: str
    status: str
    tests_passed: int
    tests_total: int
    execution_time_ms: Optional[int] = None
    error_message: Optional[str] = None
    attempt_number: int
    xp_earned: int
    created_at: datetime


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

class CodingStats(BaseModel):
    total_solved: int = 0
    total_attempts: int = 0
    total_xp: int = 0
    topics_progress: list[TopicWithProgress] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Courses (Learning Paths)
# ---------------------------------------------------------------------------

class CourseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    title_kk: Optional[str] = None
    description: Optional[str] = None
    description_kk: Optional[str] = None
    slug: str
    grade_level: Optional[int] = None
    total_lessons: int = 0
    estimated_hours: Optional[float] = None
    sort_order: int
    icon: Optional[str] = None
    is_active: bool


class CourseWithProgress(CourseResponse):
    """Course enriched with student progress."""
    completed_lessons: int = 0
    last_lesson_id: Optional[int] = None
    started: bool = False
    completed: bool = False


# ---------------------------------------------------------------------------
# Lessons
# ---------------------------------------------------------------------------

class LessonListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    title_kk: Optional[str] = None
    sort_order: int
    has_challenge: bool = False
    challenge_id: Optional[int] = None
    # Student-specific
    is_completed: bool = False


class LessonDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    course_id: int
    title: str
    title_kk: Optional[str] = None
    sort_order: int
    theory_content: str
    theory_content_kk: Optional[str] = None
    starter_code: Optional[str] = None
    challenge_id: Optional[int] = None
    challenge: Optional[ChallengeDetail] = None
    # Student-specific
    is_completed: bool = False


class LessonCompleteRequest(BaseModel):
    """Sent when student finishes reading theory (challenge completion is separate)."""
    pass


class LessonCompleteResponse(BaseModel):
    lesson_id: int
    course_id: int
    completed_lessons: int
    total_lessons: int
    course_completed: bool = False
