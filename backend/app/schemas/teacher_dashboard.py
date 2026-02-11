"""
Pydantic schemas for Teacher Dashboard API.

These schemas support:
- Dashboard overview (classes, students stats)
- Class detail with mastery distribution
- Student progress tracking
- Analytics (struggling topics, trends)
- Assignment management
"""

from typing import Optional, List, Dict
from datetime import datetime, date
from pydantic import BaseModel, Field, ConfigDict


# ============================================================================
# Brief schemas for nested responses
# ============================================================================

class StudentBriefResponse(BaseModel):
    """Brief student info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_code: str
    grade_level: int
    first_name: str
    last_name: str
    middle_name: Optional[str] = None


class ClassBriefResponse(BaseModel):
    """Brief class info for lists."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    grade_level: int
    academic_year: str
    students_count: int = 0


# ============================================================================
# Mastery-related schemas
# ============================================================================

class MasteryDistribution(BaseModel):
    """Distribution of students by mastery level (A/B/C)."""
    level_a: int = Field(0, description="Students with mastery >= 85%")
    level_b: int = Field(0, description="Students with mastery 60-84%")
    level_c: int = Field(0, description="Students with mastery < 60%")
    not_started: int = Field(0, description="Students who haven't started")

    @property
    def total(self) -> int:
        return self.level_a + self.level_b + self.level_c + self.not_started


class StudentWithMastery(BaseModel):
    """Student with their mastery information."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_code: str
    first_name: str
    last_name: str
    middle_name: Optional[str] = None

    # Mastery info
    mastery_level: Optional[str] = Field(None, description="A, B, or C")
    mastery_score: Optional[float] = Field(None, description="0-100 score")
    completed_paragraphs: int = 0
    total_paragraphs: int = 0
    progress_percentage: int = 0
    last_activity: Optional[datetime] = None


class ChapterProgressBrief(BaseModel):
    """Brief chapter progress for student detail."""
    model_config = ConfigDict(from_attributes=True)

    chapter_id: int
    chapter_title: str
    chapter_number: int
    mastery_level: Optional[str] = None
    mastery_score: Optional[float] = None
    completed_paragraphs: int = 0
    total_paragraphs: int = 0
    progress_percentage: int = 0


class TestAttemptBrief(BaseModel):
    """Brief test attempt for student history."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    test_id: int
    test_title: str
    score: float
    max_score: float
    percentage: float
    completed_at: datetime


class MasteryHistoryItem(BaseModel):
    """Single mastery history record."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    recorded_at: datetime
    previous_level: Optional[str] = None
    new_level: Optional[str] = None
    previous_score: Optional[float] = None
    new_score: Optional[float] = None
    chapter_id: Optional[int] = None
    paragraph_id: Optional[int] = None
    test_attempt_id: Optional[int] = None


# ============================================================================
# Dashboard response schemas
# ============================================================================

class RecentActivityItem(BaseModel):
    """Recent activity item for dashboard."""
    activity_type: str = Field(..., description="test_completed, paragraph_viewed, etc.")
    student_name: str
    description: str
    timestamp: datetime


class TeacherDashboardResponse(BaseModel):
    """Main dashboard response for teacher."""

    # Counts
    classes_count: int
    total_students: int

    # Mastery overview
    students_by_level: MasteryDistribution

    # Quick stats
    average_class_score: float = 0.0
    students_needing_help: int = Field(0, description="Students in level C")

    # Recent activity
    recent_activity: List[RecentActivityItem] = []


# ============================================================================
# Classes response schemas
# ============================================================================

class TeacherClassResponse(BaseModel):
    """Class info for teacher's class list."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    grade_level: int
    academic_year: str

    # Stats
    students_count: int = 0
    mastery_distribution: MasteryDistribution = Field(default_factory=MasteryDistribution)
    average_score: float = 0.0
    progress_percentage: int = 0


class TeacherClassDetailResponse(BaseModel):
    """Detailed class info with students."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str
    grade_level: int
    academic_year: str
    description: Optional[str] = None

    # Stats
    students_count: int = 0
    mastery_distribution: MasteryDistribution = Field(default_factory=MasteryDistribution)
    average_score: float = 0.0
    progress_percentage: int = 0

    # Students list
    students: List[StudentWithMastery] = []


class ClassOverviewResponse(BaseModel):
    """Class overview with analytics."""

    class_info: TeacherClassResponse

    # Per-chapter breakdown
    chapters_progress: List[ChapterProgressBrief] = []

    # Trend info
    trend: str = Field("stable", description="improving, stable, or declining")
    trend_percentage: float = 0.0


class MasteryDistributionResponse(BaseModel):
    """Detailed mastery distribution with optional filtering."""

    class_id: int
    class_name: str
    chapter_id: Optional[int] = None
    chapter_name: Optional[str] = None

    distribution: MasteryDistribution

    # Student breakdown by level
    students_level_a: List[StudentBriefResponse] = []
    students_level_b: List[StudentBriefResponse] = []
    students_level_c: List[StudentBriefResponse] = []


# ============================================================================
# Student progress response schemas
# ============================================================================

class StudentProgressDetailResponse(BaseModel):
    """Detailed student progress for teacher view."""

    # Student info
    student: StudentBriefResponse
    class_name: str

    # Overall stats
    overall_mastery_level: Optional[str] = None
    overall_mastery_score: float = 0.0
    total_time_spent: int = Field(0, description="Total seconds spent learning")

    # Progress breakdown
    chapters_progress: List[ChapterProgressBrief] = []

    # Recent tests
    recent_tests: List[TestAttemptBrief] = []

    # Activity info
    last_activity: Optional[datetime] = None
    days_since_last_activity: int = 0


class MasteryHistoryResponse(BaseModel):
    """Mastery history timeline for a student."""

    student_id: int
    student_name: str

    history: List[MasteryHistoryItem] = []


# ============================================================================
# Analytics response schemas
# ============================================================================

class StrugglingTopicResponse(BaseModel):
    """Topic where many students are struggling."""

    paragraph_id: int
    paragraph_title: str
    chapter_id: int
    chapter_title: str

    # Stats
    struggling_count: int = Field(..., description="Number of students in level C")
    total_students: int
    struggling_percentage: float
    average_score: float


class ClassTrend(BaseModel):
    """Trend data for a single class."""

    class_id: int
    class_name: str

    # Trend metrics
    previous_average: float
    current_average: float
    change_percentage: float
    trend: str = Field(..., description="improving, stable, or declining")

    # Level changes
    promoted_to_a: int = 0
    demoted_to_c: int = 0


class MasteryTrendsResponse(BaseModel):
    """Overall mastery trends across classes."""

    period: str = Field(..., description="weekly, monthly")
    start_date: date
    end_date: date

    # Overall trend
    overall_trend: str
    overall_change_percentage: float

    # Per-class breakdown
    class_trends: List[ClassTrend] = []


# ============================================================================
# Self-Assessment Analytics schemas
# ============================================================================

class SelfAssessmentParagraphSummary(BaseModel):
    """Self-assessment breakdown for a single paragraph."""

    paragraph_id: int
    paragraph_title: str
    chapter_id: int
    chapter_title: str

    total_assessments: int
    understood_count: int = 0
    questions_count: int = 0
    difficult_count: int = 0
    understood_pct: float = 0.0
    questions_pct: float = 0.0
    difficult_pct: float = 0.0


class SelfAssessmentSummaryResponse(BaseModel):
    """Aggregated self-assessment analytics for teacher's classes."""

    total_assessments: int = 0
    total_students: int = 0
    paragraphs: List[SelfAssessmentParagraphSummary] = []


class MetacognitiveAlertStudent(BaseModel):
    """Student with metacognitive mismatch."""

    student_id: int
    student_code: str
    first_name: str
    last_name: str
    paragraph_id: int
    paragraph_title: str
    rating: str
    practice_score: float
    mastery_impact: float
    created_at: datetime


class MetacognitiveAlertsResponse(BaseModel):
    """Students with overconfidence/underconfidence patterns."""

    overconfident: List[MetacognitiveAlertStudent] = Field(
        default_factory=list,
        description="Students who rated 'understood' but practice_score < 60%"
    )
    underconfident: List[MetacognitiveAlertStudent] = Field(
        default_factory=list,
        description="Students who rated 'difficult' but practice_score > 80%"
    )


class StudentSelfAssessmentItem(BaseModel):
    """Single self-assessment record for teacher view."""

    id: int
    paragraph_id: int
    paragraph_title: str
    chapter_title: str
    rating: str
    practice_score: Optional[float] = None
    mastery_impact: float
    mismatch_type: Optional[str] = Field(
        None, description="overconfident, underconfident, or null (adequate)"
    )
    created_at: datetime


class StudentSelfAssessmentHistory(BaseModel):
    """Self-assessment history for a single student."""

    student_id: int
    student_name: str
    total_assessments: int = 0
    adequate_count: int = 0
    overconfident_count: int = 0
    underconfident_count: int = 0
    assessments: List[StudentSelfAssessmentItem] = []


# ============================================================================
# Assignment schemas
# ============================================================================

class AssignmentCreate(BaseModel):
    """Schema for creating an assignment."""

    class_id: int = Field(..., description="Target class")
    title: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None

    # Content reference (optional)
    chapter_id: Optional[int] = None
    paragraph_id: Optional[int] = None
    test_id: Optional[int] = None

    # Deadline
    due_date: Optional[datetime] = None


class AssignmentUpdate(BaseModel):
    """Schema for updating an assignment."""

    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class StudentAssignmentStatus(BaseModel):
    """Student's status on an assignment."""
    model_config = ConfigDict(from_attributes=True)

    student: StudentBriefResponse
    status: str = Field(..., description="not_started, in_progress, completed, overdue")
    progress_percentage: int = 0
    score: Optional[float] = None
    completed_at: Optional[datetime] = None


class AssignmentResponse(BaseModel):
    """Assignment list item response."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    class_name: str
    title: str
    description: Optional[str] = None
    due_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    # Stats
    total_students: int = 0
    completed_count: int = 0
    completion_percentage: int = 0


class AssignmentDetailResponse(BaseModel):
    """Detailed assignment with student progress."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    class_id: int
    class_name: str
    title: str
    description: Optional[str] = None

    # Content references
    chapter_id: Optional[int] = None
    chapter_title: Optional[str] = None
    paragraph_id: Optional[int] = None
    paragraph_title: Optional[str] = None
    test_id: Optional[int] = None
    test_title: Optional[str] = None

    due_date: Optional[datetime] = None
    is_active: bool = True
    created_at: datetime

    # Student progress
    student_statuses: List[StudentAssignmentStatus] = []

    # Stats
    total_students: int = 0
    completed_count: int = 0
    in_progress_count: int = 0
    not_started_count: int = 0
    overdue_count: int = 0
