"""
Repository for ReviewSchedule data access.
"""

from typing import Optional, List
from datetime import date, timedelta
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_schedule import ReviewSchedule


class ReviewScheduleRepository:
    """Repository for ReviewSchedule CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_student_paragraph(
        self,
        student_id: int,
        paragraph_id: int
    ) -> Optional[ReviewSchedule]:
        """Get review schedule for a specific student+paragraph."""
        result = await self.db.execute(
            select(ReviewSchedule).where(
                ReviewSchedule.student_id == student_id,
                ReviewSchedule.paragraph_id == paragraph_id
            )
        )
        return result.scalar_one_or_none()

    async def get_due_reviews(
        self,
        student_id: int,
        as_of: Optional[date] = None
    ) -> List[ReviewSchedule]:
        """Get all active reviews due on or before the given date."""
        if as_of is None:
            as_of = date.today()

        result = await self.db.execute(
            select(ReviewSchedule).where(
                ReviewSchedule.student_id == student_id,
                ReviewSchedule.is_active == True,
                ReviewSchedule.next_review_date <= as_of
            ).order_by(ReviewSchedule.next_review_date)
        )
        return list(result.scalars().all())

    async def get_upcoming_count(
        self,
        student_id: int,
        days: int = 7
    ) -> int:
        """Count reviews due within the next N days (excluding today's due)."""
        today = date.today()
        end_date = today + timedelta(days=days)

        result = await self.db.execute(
            select(func.count(ReviewSchedule.id)).where(
                ReviewSchedule.student_id == student_id,
                ReviewSchedule.is_active == True,
                ReviewSchedule.next_review_date > today,
                ReviewSchedule.next_review_date <= end_date
            )
        )
        return result.scalar() or 0

    async def get_active_count(self, student_id: int) -> int:
        """Count all active review schedules for a student."""
        result = await self.db.execute(
            select(func.count(ReviewSchedule.id)).where(
                ReviewSchedule.student_id == student_id,
                ReviewSchedule.is_active == True
            )
        )
        return result.scalar() or 0

    async def get_stats(self, student_id: int) -> dict:
        """Get aggregated review stats for a student."""
        result = await self.db.execute(
            select(
                func.count(ReviewSchedule.id).label("total_active"),
                func.sum(ReviewSchedule.total_reviews).label("total_reviews"),
                func.sum(ReviewSchedule.successful_reviews).label("successful_reviews"),
                func.avg(ReviewSchedule.streak).label("avg_streak"),
            ).where(
                ReviewSchedule.student_id == student_id,
                ReviewSchedule.is_active == True
            )
        )
        row = result.one()
        total_reviews = row.total_reviews or 0
        successful = row.successful_reviews or 0

        return {
            "total_active": row.total_active or 0,
            "total_reviews": total_reviews,
            "successful_reviews": successful,
            "success_rate": (successful / total_reviews) if total_reviews > 0 else 0.0,
            "avg_streak": float(row.avg_streak or 0),
        }

    async def create(self, schedule: ReviewSchedule) -> ReviewSchedule:
        """Create a new review schedule."""
        self.db.add(schedule)
        await self.db.flush()
        return schedule

    async def save(self, schedule: ReviewSchedule) -> ReviewSchedule:
        """Save changes to an existing schedule."""
        await self.db.flush()
        return schedule
