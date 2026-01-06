"""
Student Progress Service.

Handles student progress tracking for teachers.
"""

import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chapter import Chapter
from app.models.mastery import ChapterMastery, MasteryHistory, ParagraphMastery
from app.models.school_class import SchoolClass
from app.models.student import Student
from app.models.test_attempt import TestAttempt
from app.schemas.teacher_dashboard import (
    ChapterProgressBrief,
    MasteryHistoryItem,
    MasteryHistoryResponse,
    StudentBriefResponse,
    StudentProgressDetailResponse,
    TestAttemptBrief,
)
from app.services.teacher_analytics.teacher_access_service import TeacherAccessService

logger = logging.getLogger(__name__)


class StudentProgressService:
    """Service for student progress tracking."""

    def __init__(
        self,
        db: AsyncSession,
        access_service: TeacherAccessService
    ):
        self.db = db
        self._access = access_service

    async def get_student_progress(
        self,
        teacher_id: int,
        school_id: int,
        class_id: int,
        student_id: int
    ) -> Optional[StudentProgressDetailResponse]:
        """
        Get detailed student progress.

        Args:
            teacher_id: Teacher ID
            school_id: School ID
            class_id: Class ID (for access verification)
            student_id: Student ID

        Returns:
            StudentProgressDetailResponse or None
        """
        # Verify access
        if not await self._access.verify_teacher_access_to_class(teacher_id, class_id):
            return None

        # Get student
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    not Student.is_deleted
                )
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return None

        # Get class name
        class_result = await self.db.execute(
            select(SchoolClass.name)
            .where(SchoolClass.id == class_id)
        )
        class_name = class_result.scalar() or "Unknown"

        # Get chapters progress
        chapters_progress, overall_score, overall_level = await self._get_chapters_progress(
            student_id
        )

        # Get recent tests
        recent_tests = await self._get_recent_tests(student_id)

        # Get time and activity stats
        total_time, last_activity = await self._get_activity_stats(student_id)

        days_since = 0
        if last_activity:
            days_since = (datetime.utcnow() - last_activity).days

        return StudentProgressDetailResponse(
            student=StudentBriefResponse(
                id=student.id,
                student_code=student.student_code,
                grade_level=student.grade_level,
                first_name=student.user.first_name if student.user else "",
                last_name=student.user.last_name if student.user else "",
                middle_name=student.user.middle_name if student.user else None
            ),
            class_name=class_name,
            overall_mastery_level=overall_level,
            overall_mastery_score=overall_score,
            total_time_spent=total_time,
            chapters_progress=chapters_progress,
            recent_tests=recent_tests,
            last_activity=last_activity,
            days_since_last_activity=days_since
        )

    async def get_mastery_history(
        self,
        school_id: int,
        student_id: int
    ) -> Optional[MasteryHistoryResponse]:
        """
        Get mastery history timeline for a student.

        Args:
            school_id: School ID
            student_id: Student ID

        Returns:
            MasteryHistoryResponse or None
        """
        # Get student
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    not Student.is_deleted
                )
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return None

        # Get history
        history_result = await self.db.execute(
            select(MasteryHistory)
            .where(MasteryHistory.student_id == student_id)
            .order_by(desc(MasteryHistory.recorded_at))
            .limit(50)
        )

        history = []
        for h in history_result.scalars().all():
            history.append(MasteryHistoryItem(
                id=h.id,
                recorded_at=h.recorded_at,
                previous_level=h.previous_level,
                new_level=h.new_level,
                previous_score=h.previous_score,
                new_score=h.new_score,
                chapter_id=h.chapter_id,
                paragraph_id=h.paragraph_id,
                test_attempt_id=h.test_attempt_id
            ))

        student_name = (
            f"{student.user.first_name} {student.user.last_name}"
            if student.user else "Unknown"
        )

        return MasteryHistoryResponse(
            student_id=student_id,
            student_name=student_name,
            history=history
        )

    async def _get_chapters_progress(
        self,
        student_id: int
    ) -> tuple[list, float, Optional[str]]:
        """
        Get chapters progress for a student.

        Returns:
            Tuple of (chapters_progress list, overall_score, overall_level)
        """
        chapters_result = await self.db.execute(
            select(
                Chapter.id,
                Chapter.title,
                Chapter.number,
                ChapterMastery.mastery_level,
                ChapterMastery.mastery_score,
                ChapterMastery.completed_paragraphs,
                ChapterMastery.total_paragraphs,
                ChapterMastery.progress_percentage
            )
            .join(ChapterMastery, ChapterMastery.chapter_id == Chapter.id)
            .where(ChapterMastery.student_id == student_id)
            .order_by(Chapter.number)
        )

        chapters_progress = []
        overall_score = 0.0
        overall_level = None

        for row in chapters_result.fetchall():
            ch_id, title, number, level, score, completed, total, progress = row
            chapters_progress.append(ChapterProgressBrief(
                chapter_id=ch_id,
                chapter_title=title,
                chapter_number=number,
                mastery_level=level,
                mastery_score=score,
                completed_paragraphs=completed or 0,
                total_paragraphs=total or 0,
                progress_percentage=progress or 0
            ))
            if score:
                overall_score = max(overall_score, score)
                overall_level = level

        return chapters_progress, overall_score, overall_level

    async def _get_recent_tests(
        self,
        student_id: int,
        limit: int = 10
    ) -> list:
        """Get recent test attempts for a student."""
        tests_result = await self.db.execute(
            select(TestAttempt)
            .options(selectinload(TestAttempt.test))
            .where(
                and_(
                    TestAttempt.student_id == student_id,
                    TestAttempt.status == "completed"
                )
            )
            .order_by(desc(TestAttempt.completed_at))
            .limit(limit)
        )

        recent_tests = []
        for attempt in tests_result.scalars().all():
            recent_tests.append(TestAttemptBrief(
                id=attempt.id,
                test_id=attempt.test_id,
                test_title=attempt.test.title if attempt.test else "Unknown",
                score=attempt.score * attempt.max_score,
                max_score=attempt.max_score,
                percentage=attempt.score * 100,
                completed_at=attempt.completed_at
            ))

        return recent_tests

    async def _get_activity_stats(
        self,
        student_id: int
    ) -> tuple[int, Optional[datetime]]:
        """
        Get activity statistics for a student.

        Returns:
            Tuple of (total_time_spent, last_activity_datetime)
        """
        # Get total time spent
        time_result = await self.db.execute(
            select(func.sum(ParagraphMastery.time_spent))
            .where(ParagraphMastery.student_id == student_id)
        )
        total_time = time_result.scalar() or 0

        # Get last activity
        last_activity_result = await self.db.execute(
            select(func.max(ParagraphMastery.last_updated_at))
            .where(ParagraphMastery.student_id == student_id)
        )
        last_activity = last_activity_result.scalar()

        return total_time, last_activity
