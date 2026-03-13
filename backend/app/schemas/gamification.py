"""
Gamification schemas: XP, achievements, leaderboard, daily quests.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field, field_validator


# ── Profile ──

class GamificationProfileResponse(BaseModel):
    """Student gamification profile."""
    total_xp: int
    level: int
    xp_in_current_level: int
    xp_to_next_level: int
    current_streak: int
    longest_streak: int
    badges_earned_count: int


# ── Achievements ──

class AchievementResponse(BaseModel):
    """Achievement definition."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_kk: str
    name_ru: str
    description_kk: Optional[str] = None
    description_ru: Optional[str] = None
    icon: str
    category: str
    rarity: str
    xp_reward: int


class StudentAchievementResponse(BaseModel):
    """Student achievement with progress."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    achievement: AchievementResponse
    progress: float
    is_earned: bool
    earned_at: Optional[datetime] = None


# ── Leaderboard ──

class LeaderboardEntryResponse(BaseModel):
    """Single leaderboard entry."""
    rank: int
    student_id: int
    student_name: str
    total_xp: int
    level: int


class LeaderboardResponse(BaseModel):
    """Leaderboard with student position."""
    entries: List[LeaderboardEntryResponse]
    student_rank: int
    student_xp: int
    student_level: int
    total_students: int
    scope: str  # "class" or "school"


# ── Daily Quests ──

class DailyQuestResponse(BaseModel):
    """Daily quest with student progress."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_kk: str
    name_ru: str
    description_kk: Optional[str] = None
    description_ru: Optional[str] = None
    quest_type: str
    target_value: int
    xp_reward: int
    current_value: int = 0
    is_completed: bool = False
    completed_at: Optional[datetime] = None
    subject_name_kk: Optional[str] = None
    subject_name_ru: Optional[str] = None


# ── Admin Daily Quest Schemas ──

class DailyQuestCreate(BaseModel):
    """Create a daily quest (admin)."""
    code: str = Field(max_length=50)
    name_kk: str = Field(max_length=200)
    name_ru: str = Field(max_length=200)
    description_kk: Optional[str] = None
    description_ru: Optional[str] = None
    quest_type: str
    target_value: int = Field(gt=0)
    xp_reward: int = Field(ge=0, default=0)
    is_active: bool = True
    subject_id: Optional[int] = None
    textbook_id: Optional[int] = None
    paragraph_id: Optional[int] = None

    @field_validator('paragraph_id')
    @classmethod
    def paragraph_requires_textbook(cls, v, info):
        if v is not None and not info.data.get('textbook_id'):
            raise ValueError('paragraph_id requires textbook_id')
        return v

    @field_validator('textbook_id')
    @classmethod
    def textbook_requires_subject(cls, v, info):
        if v is not None and not info.data.get('subject_id'):
            raise ValueError('textbook_id requires subject_id')
        return v


class DailyQuestUpdate(BaseModel):
    """Update a daily quest (admin)."""
    name_kk: Optional[str] = Field(None, max_length=200)
    name_ru: Optional[str] = Field(None, max_length=200)
    description_kk: Optional[str] = None
    description_ru: Optional[str] = None
    quest_type: Optional[str] = None
    target_value: Optional[int] = Field(None, gt=0)
    xp_reward: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None
    subject_id: Optional[int] = None
    textbook_id: Optional[int] = None
    paragraph_id: Optional[int] = None


class DailyQuestAdminResponse(BaseModel):
    """Daily quest admin response with denormalized names."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    code: str
    name_kk: str
    name_ru: str
    description_kk: Optional[str] = None
    description_ru: Optional[str] = None
    quest_type: str
    target_value: int
    xp_reward: int
    is_active: bool
    school_id: Optional[int] = None
    subject_id: Optional[int] = None
    textbook_id: Optional[int] = None
    paragraph_id: Optional[int] = None
    subject_name: Optional[str] = None
    textbook_title: Optional[str] = None
    paragraph_title: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── XP History ──

class XpHistoryResponse(BaseModel):
    """XP transaction entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    amount: int
    source_type: str
    source_id: Optional[int] = None
    created_at: datetime


# ── XP Award Event (returned by hooks) ──

class XpAwardResult(BaseModel):
    """Result of awarding XP."""
    amount: int
    new_total_xp: int
    new_level: int
    level_up: bool = False
    new_achievements: List[AchievementResponse] = Field(default_factory=list)
