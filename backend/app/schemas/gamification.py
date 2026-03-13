"""
Gamification schemas: XP, achievements, leaderboard, daily quests.
"""
from datetime import datetime, date
from typing import Optional, List
from pydantic import BaseModel, ConfigDict, Field


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
