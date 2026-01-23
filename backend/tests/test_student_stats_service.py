"""
Unit tests for StudentStatsService.

Tests cover:
- Streak calculation with various scenarios
- Dashboard stats aggregation
- Edge cases (no data, broken streak, etc.)
"""
import pytest
import pytest_asyncio
from datetime import datetime, timedelta, timezone, date
from unittest.mock import patch, AsyncMock

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.student_stats_service import StudentStatsService
from app.models.learning import StudentParagraph
from app.models.mastery import ParagraphMastery
from app.models.paragraph import Paragraph
from app.core.config import settings

# Note: total_tasks_completed now counts active HomeworkStudent records (not embedded answers).
# Testing homework requires complex fixtures (Homework, HomeworkStudent, Teacher, Class).
# These tests focus on streak, paragraphs, and time. Homework tests should be in integration tests.


class TestStudentStatsService:
    """Tests for StudentStatsService."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession):
        """Create service instance with test database session."""
        return StudentStatsService(db_session)

    @pytest_asyncio.fixture
    async def student_data(self, db_session: AsyncSession, test_school, test_student):
        """Setup test student data."""
        return {
            "student_id": test_student.id,
            "school_id": test_school.id,
            "db": db_session
        }

    # ========== Streak Calculation Tests ==========

    async def test_calculate_streak_no_activity(
        self, service: StudentStatsService, student_data
    ):
        """Test streak is 0 when student has no activity."""
        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 0

    async def test_calculate_streak_single_day_today(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test streak is 1 when student was active only today."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Create activity for today with sufficient time
        activity = StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,  # 10 minutes
            last_accessed_at=now,
            is_completed=False
        )
        db.add(activity)
        await db.commit()

        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 1

    async def test_calculate_streak_consecutive_days(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test streak counts consecutive active days."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Create activity for 5 consecutive days
        for days_ago in range(5):
            activity = StudentParagraph(
                student_id=student_data["student_id"],
                paragraph_id=test_paragraph.id + days_ago,  # Different paragraphs
                school_id=student_data["school_id"],
                time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,
                last_accessed_at=now - timedelta(days=days_ago),
                is_completed=False
            )
            db.add(activity)

        await db.commit()

        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 5

    async def test_calculate_streak_broken(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test streak resets when a day is missed."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Active today
        db.add(StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,
            last_accessed_at=now,
            is_completed=False
        ))

        # Skip yesterday (day 1)
        # Active 2 days ago
        db.add(StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id + 1,
            school_id=student_data["school_id"],
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,
            last_accessed_at=now - timedelta(days=2),
            is_completed=False
        ))

        await db.commit()

        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 1  # Only today counts, streak broken

    async def test_calculate_streak_insufficient_time(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test streak doesn't count days with insufficient activity time."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Activity with insufficient time (less than 10 minutes)
        activity = StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS - 1,  # Just under threshold
            last_accessed_at=now,
            is_completed=False
        )
        db.add(activity)
        await db.commit()

        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 0  # Day doesn't count

    async def test_calculate_streak_yesterday_start(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test streak can start from yesterday (if no activity today yet)."""
        db = student_data["db"]
        yesterday = datetime.now(timezone.utc) - timedelta(days=1)

        # Activity yesterday only
        activity = StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,
            last_accessed_at=yesterday,
            is_completed=False
        )
        db.add(activity)
        await db.commit()

        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 1

    async def test_calculate_streak_aggregates_multiple_paragraphs(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test streak aggregates time from multiple paragraphs on same day."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Two activities on same day, each under threshold but sum over
        half_time = settings.MIN_DAILY_ACTIVITY_SECONDS // 2 + 1

        db.add(StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            time_spent=half_time,
            last_accessed_at=now,
            is_completed=False
        ))

        db.add(StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id + 1,
            school_id=student_data["school_id"],
            time_spent=half_time,
            last_accessed_at=now,
            is_completed=False
        ))

        await db.commit()

        streak = await service.calculate_streak(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )
        assert streak == 1

    # ========== Dashboard Stats Tests ==========

    async def test_get_dashboard_stats_empty(
        self, service: StudentStatsService, student_data
    ):
        """Test dashboard stats when student has no activity."""
        stats = await service.get_dashboard_stats(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )

        assert stats.streak_days == 0
        assert stats.total_paragraphs_completed == 0
        assert stats.total_tasks_completed == 0
        assert stats.total_time_spent_minutes == 0

    async def test_get_dashboard_stats_with_activity(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test dashboard stats with various activities."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Add StudentParagraph records for time tracking and streak calculation
        for i in range(3):
            db.add(StudentParagraph(
                student_id=student_data["student_id"],
                paragraph_id=test_paragraph.id + i,
                school_id=student_data["school_id"],
                time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,
                last_accessed_at=now - timedelta(days=i),
                is_completed=True
            ))

        # Add ParagraphMastery records for completed paragraphs count
        # (paragraphs_completed now uses ParagraphMastery.is_completed)
        for i in range(3):
            db.add(ParagraphMastery(
                student_id=student_data["student_id"],
                paragraph_id=test_paragraph.id + i,
                school_id=student_data["school_id"],
                is_completed=True,
                status="mastered"
            ))

        # Note: total_tasks_completed now counts active HomeworkStudent records.
        # Creating homework requires Teacher, Class fixtures - tested in integration tests.

        await db.commit()

        stats = await service.get_dashboard_stats(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )

        assert stats.streak_days == 3
        assert stats.total_paragraphs_completed == 3
        assert stats.total_tasks_completed == 0  # No homework assigned in this test
        assert stats.total_time_spent_minutes == 30  # 3 * 600 seconds = 1800 / 60 = 30 min

    async def test_get_dashboard_stats_school_isolation(
        self, service: StudentStatsService, student_data, test_paragraph
    ):
        """Test that stats only include data from student's school."""
        db = student_data["db"]
        now = datetime.now(timezone.utc)

        # Add StudentParagraph for time tracking (correct school)
        db.add(StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS,
            last_accessed_at=now,
            is_completed=True
        ))

        # Add ParagraphMastery for completed count (correct school)
        db.add(ParagraphMastery(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id,
            school_id=student_data["school_id"],
            is_completed=True,
            status="mastered"
        ))

        # Add StudentParagraph for different school (should be ignored for time)
        db.add(StudentParagraph(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id + 1,
            school_id=student_data["school_id"] + 9999,  # Different school
            time_spent=settings.MIN_DAILY_ACTIVITY_SECONDS * 10,
            last_accessed_at=now,
            is_completed=True
        ))

        # Add ParagraphMastery for different school (should be ignored for completed count)
        db.add(ParagraphMastery(
            student_id=student_data["student_id"],
            paragraph_id=test_paragraph.id + 1,
            school_id=student_data["school_id"] + 9999,  # Different school
            is_completed=True,
            status="mastered"
        ))

        await db.commit()

        stats = await service.get_dashboard_stats(
            student_id=student_data["student_id"],
            school_id=student_data["school_id"]
        )

        assert stats.total_paragraphs_completed == 1  # Only from correct school
        assert stats.total_time_spent_minutes == 10  # 600 / 60 = 10 min
