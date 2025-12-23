"""
Student Stats API endpoints.

This module provides endpoints for students to:
- View dashboard statistics including streak
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
)
from app.models.user import User
from app.models.learning import StudentParagraph
from app.models.embedded_question import StudentEmbeddedAnswer
from app.schemas.student_content import StudentDashboardStats


router = APIRouter()
logger = logging.getLogger(__name__)


async def calculate_streak(db: AsyncSession, student_id: int, school_id: int) -> int:
    """
    Calculate consecutive active days streak.

    Active day = day with >= 600 seconds (10 minutes) of paragraph activity.
    Uses StudentParagraph.last_accessed_at and time_spent.

    Algorithm:
    1. Get daily time spent aggregated by date
    2. Filter days with >= 600 seconds
    3. Count consecutive days backwards from today/yesterday

    Args:
        db: Database session
        student_id: Student ID
        school_id: School ID for data isolation

    Returns:
        Number of consecutive active days (streak)
    """
    # Get daily time totals for active days (>= 10 minutes)
    daily_time_query = (
        select(
            cast(StudentParagraph.last_accessed_at, Date).label('activity_date'),
            func.sum(StudentParagraph.time_spent).label('total_time')
        )
        .where(
            StudentParagraph.student_id == student_id,
            StudentParagraph.school_id == school_id,
            StudentParagraph.last_accessed_at.isnot(None)
        )
        .group_by(cast(StudentParagraph.last_accessed_at, Date))
        .having(func.sum(StudentParagraph.time_spent) >= 600)  # 10 minutes minimum
        .order_by(cast(StudentParagraph.last_accessed_at, Date).desc())
    )

    result = await db.execute(daily_time_query)
    rows = result.fetchall()
    active_days = [row.activity_date for row in rows]

    if not active_days:
        return 0

    # Check if streak is still active (today or yesterday was active)
    today = date.today()
    yesterday = today - timedelta(days=1)

    if active_days[0] not in (today, yesterday):
        return 0  # Streak broken

    # Count consecutive days backwards
    streak = 0
    expected_date = active_days[0]

    for active_date in active_days:
        if active_date == expected_date:
            streak += 1
            expected_date = expected_date - timedelta(days=1)
        else:
            break

    return streak


@router.get("/stats", response_model=StudentDashboardStats)
async def get_student_stats(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student's overall statistics including streak.

    Returns:
    - streak_days: Consecutive days of learning (>= 10 minutes per day)
    - total_paragraphs_completed: Number of completed paragraphs
    - total_tasks_completed: Number of embedded questions answered
    - total_time_spent_minutes: Total learning time in minutes
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # 1. Calculate total paragraphs completed
    completed_count_result = await db.execute(
        select(func.count(StudentParagraph.id)).where(
            StudentParagraph.student_id == student_id,
            StudentParagraph.school_id == school_id,
            StudentParagraph.is_completed == True
        )
    )
    total_paragraphs_completed = completed_count_result.scalar() or 0

    # 2. Calculate total tasks (embedded questions) answered
    tasks_count_result = await db.execute(
        select(func.count(StudentEmbeddedAnswer.id)).where(
            StudentEmbeddedAnswer.student_id == student_id,
            StudentEmbeddedAnswer.school_id == school_id
        )
    )
    total_tasks_completed = tasks_count_result.scalar() or 0

    # 3. Calculate total time spent (sum of all paragraph time_spent)
    time_result = await db.execute(
        select(func.sum(StudentParagraph.time_spent)).where(
            StudentParagraph.student_id == student_id,
            StudentParagraph.school_id == school_id
        )
    )
    total_time_spent_seconds = time_result.scalar() or 0
    total_time_spent_minutes = total_time_spent_seconds // 60

    # 4. Calculate streak
    streak_days = await calculate_streak(db, student_id, school_id)

    logger.info(
        f"Student {student_id} stats: streak={streak_days}, "
        f"paragraphs={total_paragraphs_completed}, tasks={total_tasks_completed}, "
        f"time={total_time_spent_minutes}min"
    )

    return StudentDashboardStats(
        streak_days=streak_days,
        total_paragraphs_completed=total_paragraphs_completed,
        total_tasks_completed=total_tasks_completed,
        total_time_spent_minutes=total_time_spent_minutes
    )
