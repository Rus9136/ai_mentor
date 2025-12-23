"""
Student Stats API endpoints.

This module provides endpoints for students to:
- View dashboard statistics including streak

All business logic is delegated to StudentStatsService.
"""

import logging

from fastapi import APIRouter, Depends

from app.api.dependencies import (
    get_current_user_school_id,
    get_student_from_user,
    get_student_stats_service,
)
from app.models.student import Student
from app.services.student_stats_service import StudentStatsService
from app.schemas.student_content import StudentDashboardStats


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/stats", response_model=StudentDashboardStats)
async def get_student_stats(
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: StudentStatsService = Depends(get_student_stats_service)
):
    """
    Get student's overall statistics including streak.

    Returns:
    - streak_days: Consecutive days of learning (>= 10 minutes per day)
    - total_paragraphs_completed: Number of completed paragraphs
    - total_tasks_completed: Number of embedded questions answered
    - total_time_spent_minutes: Total learning time in minutes
    """
    return await service.get_dashboard_stats(student.id, school_id)
