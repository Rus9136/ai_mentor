"""
Student Statistics Service.

This service handles calculation of student dashboard statistics including:
- Streak calculation (consecutive active days)
- Total paragraphs completed
- Active homework tasks (not yet submitted)
- Total time spent learning

The service is read-only and does not modify data, so no commit is needed.
"""

import logging
from datetime import date, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, cast, Date

from app.models.learning import StudentParagraph
from app.models.mastery import ParagraphMastery
from app.models.homework import HomeworkStudent, Homework, HomeworkStatus, HomeworkStudentStatus
from app.schemas.student_content import StudentDashboardStats
from app.core.config import settings

logger = logging.getLogger(__name__)


class StudentStatsService:
    """
    Service for calculating student statistics.

    Responsibilities:
    - Calculate streak (consecutive active days)
    - Aggregate time spent learning
    - Count completed paragraphs and answered tasks

    Note: This service only reads data, commit is not required.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    async def calculate_streak(
        self,
        student_id: int,
        school_id: int
    ) -> int:
        """
        Calculate streak - number of consecutive active days.

        An active day is defined as a day with >= MIN_DAILY_ACTIVITY_SECONDS
        seconds of paragraph activity. Streak is counted backwards from
        today or yesterday.

        Uses index: idx_student_paragraph_streak for performance.

        Args:
            student_id: Student ID
            school_id: School ID for data isolation

        Returns:
            Number of consecutive active days
        """
        min_seconds = settings.MIN_DAILY_ACTIVITY_SECONDS

        # Get days with sufficient activity
        # Uses index idx_student_paragraph_streak
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
            .having(func.sum(StudentParagraph.time_spent) >= min_seconds)
            .order_by(cast(StudentParagraph.last_accessed_at, Date).desc())
        )

        result = await self.db.execute(daily_time_query)
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

    async def get_dashboard_stats(
        self,
        student_id: int,
        school_id: int
    ) -> StudentDashboardStats:
        """
        Get complete dashboard statistics for a student.

        Aggregates:
        - streak_days: Consecutive active learning days
        - total_paragraphs_completed: Number of fully completed paragraphs
        - total_tasks_completed: Number of active homework assignments (not yet submitted)
        - total_time_spent_minutes: Total learning time in minutes

        Args:
            student_id: Student ID
            school_id: School ID for data isolation

        Returns:
            StudentDashboardStats with all aggregated statistics
        """
        # 1. Count completed paragraphs (from ParagraphMastery for consistency with UI progress)
        # Note: ParagraphMastery.is_completed is set when student passes a test for the paragraph
        # This ensures stats match the progress shown in textbook/chapter views
        completed_result = await self.db.execute(
            select(func.count(ParagraphMastery.id)).where(
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.school_id == school_id,
                ParagraphMastery.is_completed == True
            )
        )
        total_paragraphs_completed = completed_result.scalar() or 0

        # 2. Count active homework assignments (not yet submitted)
        # Active = Homework is PUBLISHED and student status is ASSIGNED or IN_PROGRESS
        active_tasks_result = await self.db.execute(
            select(func.count(HomeworkStudent.id))
            .join(Homework, HomeworkStudent.homework_id == Homework.id)
            .where(
                HomeworkStudent.student_id == student_id,
                HomeworkStudent.school_id == school_id,
                Homework.status == HomeworkStatus.PUBLISHED,
                HomeworkStudent.status.in_([
                    HomeworkStudentStatus.ASSIGNED,
                    HomeworkStudentStatus.IN_PROGRESS
                ])
            )
        )
        total_tasks_pending = active_tasks_result.scalar() or 0

        # 3. Sum total time spent
        time_result = await self.db.execute(
            select(func.sum(StudentParagraph.time_spent)).where(
                StudentParagraph.student_id == student_id,
                StudentParagraph.school_id == school_id
            )
        )
        total_time_seconds = time_result.scalar() or 0
        total_time_minutes = total_time_seconds // 60

        # 4. Calculate streak
        streak_days = await self.calculate_streak(student_id, school_id)

        logger.info(
            f"Student {student_id} stats: streak={streak_days}, "
            f"paragraphs={total_paragraphs_completed}, pending_tasks={total_tasks_pending}, "
            f"time={total_time_minutes}min"
        )

        return StudentDashboardStats(
            streak_days=streak_days,
            total_paragraphs_completed=total_paragraphs_completed,
            total_tasks_completed=total_tasks_pending,  # Now counts active homework, not embedded questions
            total_time_spent_minutes=total_time_minutes
        )
