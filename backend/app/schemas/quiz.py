"""
Schemas for Quiz Battle.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ──

class QuizSessionSettings(BaseModel):
    time_per_question_ms: int = Field(default=30000, ge=5000, le=120000, description="Time per question in ms")
    show_leaderboard: bool = Field(default=True)


class QuizSessionCreate(BaseModel):
    test_id: int
    class_id: Optional[int] = None
    settings: QuizSessionSettings = Field(default_factory=QuizSessionSettings)


class JoinQuizRequest(BaseModel):
    join_code: str = Field(min_length=4, max_length=6)


# ── Response schemas ──

class QuizParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: str = ""
    total_score: int = 0
    correct_answers: int = 0
    rank: Optional[int] = None
    xp_earned: int = 0
    joined_at: datetime


class QuizSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    teacher_id: int
    class_id: Optional[int] = None
    test_id: int
    test_title: str = ""
    class_name: str = ""
    join_code: str
    status: str
    settings: dict = {}
    question_count: int
    current_question_index: int
    participant_count: int = 0
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None
    created_at: datetime


class QuizSessionDetailResponse(QuizSessionResponse):
    participants: list[QuizParticipantResponse] = []


class JoinQuizResponse(BaseModel):
    quiz_session_id: int
    ws_url: str
    status: str
    participant_count: int = 0


class QuizQuestionOut(BaseModel):
    index: int
    text: str
    options: list[str]
    time_limit_ms: int
    image_url: Optional[str] = None


class QuizResultsResponse(BaseModel):
    quiz_session_id: int
    test_title: str = ""
    total_questions: int
    leaderboard: list[QuizParticipantResponse] = []
    your_rank: Optional[int] = None
    your_score: Optional[int] = None
    your_correct: Optional[int] = None
    xp_earned: Optional[int] = None
    stats: dict = {}


class QuizTestInfo(BaseModel):
    """Test info for quiz creation."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: Optional[str] = None
    question_count: int = 0
    difficulty: str = "medium"
    test_purpose: str = "formative"
