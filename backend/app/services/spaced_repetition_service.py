"""
Spaced Repetition Service.

Implements the Leitner system for scheduling paragraph reviews
with increasing intervals after mastery is achieved.

Intervals (by streak level):
    0: 1 day, 1: 3 days, 2: 7 days, 3: 14 days,
    4: 30 days, 5: 60 days, 6: 120 days (max)
"""

import logging
from datetime import date, datetime, timezone, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review_schedule import ReviewSchedule
from app.repositories.review_schedule_repo import ReviewScheduleRepository
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository

logger = logging.getLogger(__name__)

# Leitner intervals: streak level → days until next review
INTERVALS = {
    0: 1,
    1: 3,
    2: 7,
    3: 14,
    4: 30,
    5: 60,
    6: 120,
}

MAX_STREAK = 6

# Review quiz pass threshold
REVIEW_PASS_THRESHOLD = 0.80


class SpacedRepetitionService:
    """Service for managing spaced repetition schedules."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.review_repo = ReviewScheduleRepository(db)
        self.mastery_repo = ParagraphMasteryRepository(db)

    async def activate_review(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
    ) -> ReviewSchedule:
        """
        Activate spaced repetition for a paragraph (called when mastered).

        If schedule already exists, reactivate it and reset streak.
        Otherwise create a new one.
        """
        existing = await self.review_repo.get_by_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id,
        )

        tomorrow = date.today() + timedelta(days=INTERVALS[0])

        if existing:
            existing.is_active = True
            existing.streak = 0
            existing.next_review_date = tomorrow
            await self.review_repo.save(existing)
            logger.info(
                f"Reactivated review schedule: student={student_id}, "
                f"paragraph={paragraph_id}, next={tomorrow}"
            )
            return existing

        schedule = ReviewSchedule(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            streak=0,
            next_review_date=tomorrow,
            is_active=True,
        )
        await self.review_repo.create(schedule)
        logger.info(
            f"Created review schedule: student={student_id}, "
            f"paragraph={paragraph_id}, next={tomorrow}"
        )
        return schedule

    async def process_review_result(
        self,
        student_id: int,
        paragraph_id: int,
        score: float,
    ) -> dict:
        """
        Process the result of a review quiz.

        On pass (≥80%):
          - streak += 1 (max 6)
          - next_review in INTERVALS[new_streak] days
          - refresh paragraph_mastery.last_updated_at (resets time decay)

        On fail (<80%):
          - streak = max(streak - 2, 0)
          - next_review in INTERVALS[new_streak] days
          - DO NOT refresh last_updated_at (decay continues)

        Returns:
            dict with passed, new_streak, next_review_date, message
        """
        schedule = await self.review_repo.get_by_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id,
        )

        if not schedule or not schedule.is_active:
            raise ValueError(f"No active review schedule for paragraph {paragraph_id}")

        passed = score >= REVIEW_PASS_THRESHOLD
        now = datetime.now(timezone.utc)

        # Update streak
        if passed:
            new_streak = min(schedule.streak + 1, MAX_STREAK)
            schedule.successful_reviews += 1
        else:
            new_streak = max(schedule.streak - 2, 0)

        # Calculate next review date
        interval = INTERVALS[new_streak]
        next_date = date.today() + timedelta(days=interval)

        # Update schedule
        schedule.streak = new_streak
        schedule.next_review_date = next_date
        schedule.last_review_date = now
        schedule.total_reviews += 1
        await self.review_repo.save(schedule)

        # On success: refresh paragraph mastery last_updated_at (resets time decay)
        if passed:
            mastery = await self.mastery_repo.get_by_student_paragraph(
                student_id=student_id,
                paragraph_id=paragraph_id,
            )
            if mastery:
                mastery.last_updated_at = now
                await self.db.flush()
                logger.info(
                    f"Refreshed mastery last_updated_at for student={student_id}, "
                    f"paragraph={paragraph_id} (decay reset)"
                )

        await self.db.commit()

        # Build response message
        if passed:
            if new_streak >= 5:
                message = "Отлично! Материал прочно закреплён. Следующая проверка нескоро."
            elif new_streak >= 3:
                message = "Хорошо! Знания укрепляются. Интервал увеличен."
            else:
                message = "Правильно! Продолжай в том же духе."
        else:
            message = "Стоит повторить этот материал. Проверка назначена раньше."

        logger.info(
            f"Review processed: student={student_id}, paragraph={paragraph_id}, "
            f"score={score:.2f}, passed={passed}, streak={new_streak}, next={next_date}"
        )

        return {
            "passed": passed,
            "score": score,
            "new_streak": new_streak,
            "next_review_date": next_date,
            "message": message,
        }

    async def deactivate_review(
        self,
        student_id: int,
        paragraph_id: int,
    ) -> None:
        """Deactivate review schedule (e.g., when mastery drops below threshold)."""
        schedule = await self.review_repo.get_by_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id,
        )
        if schedule and schedule.is_active:
            schedule.is_active = False
            await self.review_repo.save(schedule)
            logger.info(
                f"Deactivated review: student={student_id}, paragraph={paragraph_id}"
            )
