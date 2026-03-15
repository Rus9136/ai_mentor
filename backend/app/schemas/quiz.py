"""
Schemas for Quiz Battle.
Supports: classic, team, self_paced, quick_question modes.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field


# ── Request schemas ──

class QuizSessionSettings(BaseModel):
    time_per_question_ms: int = Field(default=30000, ge=5000, le=120000, description="Time per question in ms")
    show_leaderboard: bool = Field(default=True)
    shuffle_questions: bool = Field(default=False, description="Randomize question order")
    shuffle_answers: bool = Field(default=False, description="Randomize answer options per question")
    scoring_mode: str = Field(default="speed", description="'speed' (time-based) or 'accuracy' (1000 per correct)")
    # Phase 2.2: game modes
    mode: str = Field(default="classic", description="classic|team|self_paced|quick_question")
    # Phase 2.3: pacing
    pacing: str = Field(default="timed", description="'timed' (countdown) or 'teacher_paced' (manual, no timer)")
    team_count: Optional[int] = Field(default=None, ge=2, le=6, description="Number of teams (team mode)")
    show_space_race: bool = Field(default=False, description="Show space race visualization (team mode)")
    deadline: Optional[str] = Field(default=None, description="ISO datetime deadline (self_paced mode)")
    # Phase 2.4: gamification
    enable_powerups: bool = Field(default=False, description="Allow students to use power-ups (timed mode only)")
    enable_confidence_mode: bool = Field(default=False, description="Risk/Safe choice per question (speed mode only)")


class QuizSessionCreate(BaseModel):
    test_id: Optional[int] = None  # nullable for quick_question mode
    class_id: Optional[int] = None
    settings: QuizSessionSettings = Field(default_factory=QuizSessionSettings)


class JoinQuizRequest(BaseModel):
    join_code: str = Field(min_length=4, max_length=6)


class QuickQuestionCreate(BaseModel):
    """Create a quick question session (no test needed)."""
    class_id: Optional[int] = None
    question_text: str = Field(min_length=1, max_length=1000)
    options: list[str] = Field(min_length=2, max_length=6)
    time_per_question_ms: int = Field(default=30000, ge=5000, le=120000)


class SelfPacedSubmitRequest(BaseModel):
    """Submit an answer in self-paced mode."""
    question_index: int = Field(ge=0)
    selected_option: int = Field(ge=0)


# ── Response schemas ──

class QuizParticipantResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    student_id: int
    student_name: str = ""
    total_score: int = 0
    correct_answers: int = 0
    current_streak: int = 0
    max_streak: int = 0
    rank: Optional[int] = None
    xp_earned: int = 0
    joined_at: datetime
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    team_color: Optional[str] = None


class QuizTeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    color: str
    total_score: int = 0
    correct_answers: int = 0
    member_count: int = 0


class QuizSessionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    teacher_id: int
    class_id: Optional[int] = None
    test_id: Optional[int] = None
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
    teams: list[QuizTeamResponse] = []


class QuizSessionDetailResponse(QuizSessionResponse):
    participants: list[QuizParticipantResponse] = []


class JoinQuizResponse(BaseModel):
    quiz_session_id: int
    ws_url: str
    status: str
    participant_count: int = 0
    mode: str = "classic"
    team_id: Optional[int] = None
    team_name: Optional[str] = None
    team_color: Optional[str] = None


class QuizQuestionOut(BaseModel):
    index: int
    text: str
    question_type: str = "single_choice"  # single_choice | short_answer
    options: list[str]
    time_limit_ms: int
    image_url: Optional[str] = None


class QuizResultsResponse(BaseModel):
    quiz_session_id: int
    test_title: str = ""
    total_questions: int
    leaderboard: list[QuizParticipantResponse] = []
    team_leaderboard: list[QuizTeamResponse] = []
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


# ── Self-Paced schemas ──

class SelfPacedNextQuestion(BaseModel):
    question: QuizQuestionOut
    answered_count: int
    total_questions: int
    is_last: bool


class SelfPacedAnswerResult(BaseModel):
    is_correct: bool
    correct_option: int
    score: int
    total_score: int
    correct_answers: int
    answered_count: int
    total_questions: int
    is_finished: bool


# ── Student progress (teacher view) ──

class StudentProgressItem(BaseModel):
    student_id: int
    student_name: str
    answered: int
    total: int
    correct: int
    total_score: int


# ── Student quiz list (My Quizzes widget) ──

class StudentQuizListItem(BaseModel):
    """Quiz item for student's "My Quizzes" widget."""
    id: int
    test_title: str = ""
    class_name: str = ""
    join_code: str
    status: str
    mode: str = "classic"
    question_count: int = 0
    participant_count: int = 0
    has_joined: bool = False
    answered_count: int = 0
    total_score: Optional[int] = None
    correct_answers: Optional[int] = None
    rank: Optional[int] = None
    xp_earned: Optional[int] = None
    created_at: datetime


# ── Matrix schemas (Phase 2.3) ──

class QuizMatrixAnswer(BaseModel):
    question_index: int
    is_correct: bool
    answer_time_ms: int
    text_answer: Optional[str] = None

class QuizMatrixStudent(BaseModel):
    student_id: int
    student_name: str
    answers: list[Optional[QuizMatrixAnswer]]

class QuizMatrixResponse(BaseModel):
    students: list[QuizMatrixStudent]
    question_count: int
