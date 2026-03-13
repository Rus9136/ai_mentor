"""
Student Gamification API endpoints.

Provides XP profile, achievements, leaderboard, daily quests, and XP history.
"""
import logging
from datetime import date
from typing import Optional, List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.student import Student
from app.api.dependencies import get_student_from_user, get_current_user_school_id
from app.schemas.gamification import (
    GamificationProfileResponse,
    StudentAchievementResponse,
    AchievementResponse,
    LeaderboardResponse,
    LeaderboardEntryResponse,
    DailyQuestResponse,
    XpHistoryResponse,
)
from app.services.gamification_service import GamificationService
from app.repositories.gamification_repo import GamificationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/gamification")


@router.get("/profile", response_model=GamificationProfileResponse)
async def get_gamification_profile(
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get student's gamification profile (XP, level, streak, badges count)."""
    repo = GamificationRepository(db)
    level, xp_in_current, xp_to_next = GamificationService.calculate_level(student.total_xp)
    badges_count = await repo.count_earned_achievements(student.id)

    return GamificationProfileResponse(
        total_xp=student.total_xp,
        level=level,
        xp_in_current_level=xp_in_current,
        xp_to_next_level=xp_to_next,
        current_streak=student.current_streak,
        longest_streak=student.longest_streak,
        badges_earned_count=badges_count,
    )


@router.get("/achievements", response_model=List[StudentAchievementResponse])
async def get_achievements(
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all achievements with student progress."""
    repo = GamificationRepository(db)

    # Get all active achievements
    all_achievements = await repo.get_all_active_achievements()
    student_achievements = await repo.get_student_achievements(student.id)

    # Build map of student progress
    sa_map = {sa.achievement_id: sa for sa in student_achievements}

    result = []
    for ach in all_achievements:
        sa = sa_map.get(ach.id)
        result.append(StudentAchievementResponse(
            id=sa.id if sa else 0,
            achievement=AchievementResponse.model_validate(ach),
            progress=sa.progress if sa else 0.0,
            is_earned=sa.is_earned if sa else False,
            earned_at=sa.earned_at if sa else None,
        ))

    return result


@router.get("/achievements/recent", response_model=List[StudentAchievementResponse])
async def get_recent_achievements(
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get recently earned but unnotified achievements. Marks them as notified."""
    repo = GamificationRepository(db)
    unnotified = await repo.get_unnotified_achievements(student.id)

    result = [
        StudentAchievementResponse(
            id=sa.id,
            achievement=AchievementResponse.model_validate(sa.achievement),
            progress=sa.progress,
            is_earned=sa.is_earned,
            earned_at=sa.earned_at,
        )
        for sa in unnotified
    ]

    # Mark as notified
    if unnotified:
        await repo.mark_achievements_notified(
            student.id, [sa.achievement_id for sa in unnotified]
        )
        await db.commit()

    return result


@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    scope: str = Query("school", pattern="^(school|class)$"),
    class_id: Optional[int] = Query(None),
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get leaderboard for school or class scope."""
    repo = GamificationRepository(db)

    if scope == "class" and class_id:
        entries = await repo.get_class_leaderboard(school_id, class_id)
        rank = await repo.get_student_rank(student.id, school_id, class_id)
        total = await repo.get_school_student_count(school_id, class_id)
    else:
        entries = await repo.get_school_leaderboard(school_id)
        rank = await repo.get_student_rank(student.id, school_id)
        total = await repo.get_school_student_count(school_id)

    level, _, _ = GamificationService.calculate_level(student.total_xp)

    return LeaderboardResponse(
        entries=[LeaderboardEntryResponse(**e) for e in entries],
        student_rank=rank,
        student_xp=student.total_xp,
        student_level=level,
        total_students=total,
        scope=scope,
    )


@router.get("/daily-quests", response_model=List[DailyQuestResponse])
async def get_daily_quests(
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get today's daily quests with progress."""
    repo = GamificationRepository(db)
    today = date.today()

    # Lazy assign quests for today
    await repo.ensure_daily_quests_assigned(student.id, school_id, today)
    await db.commit()

    pairs = await repo.get_student_daily_quests(student.id, today)

    return [
        DailyQuestResponse(
            id=quest.id,
            code=quest.code,
            name_kk=quest.name_kk,
            name_ru=quest.name_ru,
            description_kk=quest.description_kk,
            description_ru=quest.description_ru,
            quest_type=quest.quest_type.value if hasattr(quest.quest_type, 'value') else quest.quest_type,
            target_value=quest.target_value,
            xp_reward=quest.xp_reward,
            current_value=sdq.current_value if sdq else 0,
            is_completed=sdq.is_completed if sdq else False,
            completed_at=sdq.completed_at if sdq else None,
        )
        for quest, sdq in pairs
    ]


@router.get("/xp-history", response_model=List[XpHistoryResponse])
async def get_xp_history(
    days: int = Query(7, ge=1, le=90),
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get XP transaction history."""
    repo = GamificationRepository(db)
    transactions = await repo.get_xp_history(student.id, days)

    return [
        XpHistoryResponse(
            id=txn.id,
            amount=txn.amount,
            source_type=txn.source_type.value if hasattr(txn.source_type, 'value') else txn.source_type,
            source_id=txn.source_id,
            created_at=txn.created_at,
        )
        for txn in transactions
    ]
