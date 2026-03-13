"""
Teacher Gamification API endpoints.

Provides class leaderboard and achievement summaries for teachers.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.teacher import Teacher
from app.api.dependencies import get_teacher_from_user, get_current_user_school_id
from app.schemas.gamification import LeaderboardResponse, LeaderboardEntryResponse
from app.services.gamification_service import GamificationService
from app.repositories.gamification_repo import GamificationRepository

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/gamification", tags=["Teachers - Gamification"])


@router.get("/class/{class_id}/leaderboard", response_model=LeaderboardResponse)
async def get_class_leaderboard(
    class_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get class leaderboard for teacher's class."""
    repo = GamificationRepository(db)

    entries = await repo.get_class_leaderboard(school_id, class_id)
    total = await repo.get_school_student_count(school_id, class_id)

    return LeaderboardResponse(
        entries=[LeaderboardEntryResponse(**e) for e in entries],
        student_rank=0,
        student_xp=0,
        student_level=0,
        total_students=total,
        scope="class",
    )
