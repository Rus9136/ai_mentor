"""
Repository for coding challenges and courses data access.
"""
from typing import Optional
from sqlalchemy import select, func, and_, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.coding import (
    CodingTopic,
    CodingChallenge,
    CodingSubmission,
    CodingCourse,
    CodingLesson,
    CodingCourseProgress,
)


class CodingRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Topics
    # -----------------------------------------------------------------------

    async def list_topics(self, active_only: bool = True) -> list[CodingTopic]:
        query = (
            select(CodingTopic)
            .order_by(CodingTopic.sort_order)
        )
        if active_only:
            query = query.where(CodingTopic.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_topic_by_slug(self, slug: str) -> Optional[CodingTopic]:
        result = await self.db.execute(
            select(CodingTopic).where(CodingTopic.slug == slug)
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Challenges
    # -----------------------------------------------------------------------

    async def list_challenges_by_topic(
        self, topic_id: int, active_only: bool = True
    ) -> list[CodingChallenge]:
        query = (
            select(CodingChallenge)
            .where(CodingChallenge.topic_id == topic_id)
            .order_by(CodingChallenge.sort_order)
        )
        if active_only:
            query = query.where(CodingChallenge.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_challenge_by_id(self, challenge_id: int) -> Optional[CodingChallenge]:
        result = await self.db.execute(
            select(CodingChallenge).where(CodingChallenge.id == challenge_id)
        )
        return result.scalar_one_or_none()

    async def count_challenges_by_topic(self, topic_ids: list[int]) -> dict[int, int]:
        """Return {topic_id: count} for active challenges."""
        result = await self.db.execute(
            select(
                CodingChallenge.topic_id,
                func.count(CodingChallenge.id),
            )
            .where(
                CodingChallenge.topic_id.in_(topic_ids),
                CodingChallenge.is_active == True,
            )
            .group_by(CodingChallenge.topic_id)
        )
        return {row[0]: row[1] for row in result.all()}

    # -----------------------------------------------------------------------
    # Submissions
    # -----------------------------------------------------------------------

    async def create_submission(
        self,
        student_id: int,
        school_id: int,
        challenge_id: int,
        code: str,
        status: str,
        tests_passed: int,
        tests_total: int,
        execution_time_ms: Optional[int],
        error_message: Optional[str],
        attempt_number: int,
        xp_earned: int,
    ) -> CodingSubmission:
        sub = CodingSubmission(
            student_id=student_id,
            school_id=school_id,
            challenge_id=challenge_id,
            code=code,
            status=status,
            tests_passed=tests_passed,
            tests_total=tests_total,
            execution_time_ms=execution_time_ms,
            error_message=error_message,
            attempt_number=attempt_number,
            xp_earned=xp_earned,
        )
        self.db.add(sub)
        await self.db.flush()
        await self.db.refresh(sub)
        return sub

    async def get_attempts_count(self, student_id: int, challenge_id: int) -> int:
        result = await self.db.execute(
            select(func.count(CodingSubmission.id)).where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id == challenge_id,
            )
        )
        return result.scalar() or 0

    async def has_passed(self, student_id: int, challenge_id: int) -> bool:
        result = await self.db.execute(
            select(CodingSubmission.id).where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id == challenge_id,
                CodingSubmission.status == "passed",
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None

    async def get_solved_challenge_ids(
        self, student_id: int, challenge_ids: list[int]
    ) -> set[int]:
        """Return set of challenge IDs that the student has passed."""
        if not challenge_ids:
            return set()
        result = await self.db.execute(
            select(CodingSubmission.challenge_id)
            .where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id.in_(challenge_ids),
                CodingSubmission.status == "passed",
            )
            .distinct()
        )
        return {row[0] for row in result.all()}

    async def get_attempted_challenge_ids(
        self, student_id: int, challenge_ids: list[int]
    ) -> set[int]:
        """Return set of challenge IDs that the student attempted (any status)."""
        if not challenge_ids:
            return set()
        result = await self.db.execute(
            select(CodingSubmission.challenge_id)
            .where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id.in_(challenge_ids),
            )
            .distinct()
        )
        return {row[0] for row in result.all()}

    async def get_best_submission(
        self, student_id: int, challenge_id: int
    ) -> Optional[CodingSubmission]:
        """Best = passed with most tests_passed, or latest attempt if none passed."""
        # First try passed
        result = await self.db.execute(
            select(CodingSubmission)
            .where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id == challenge_id,
                CodingSubmission.status == "passed",
            )
            .order_by(CodingSubmission.tests_passed.desc())
            .limit(1)
        )
        sub = result.scalar_one_or_none()
        if sub:
            return sub

        # Fallback to latest attempt
        result = await self.db.execute(
            select(CodingSubmission)
            .where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id == challenge_id,
            )
            .order_by(CodingSubmission.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def list_submissions(
        self, student_id: int, challenge_id: int, limit: int = 20
    ) -> list[CodingSubmission]:
        result = await self.db.execute(
            select(CodingSubmission)
            .where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.challenge_id == challenge_id,
            )
            .order_by(CodingSubmission.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    # -----------------------------------------------------------------------
    # Stats
    # -----------------------------------------------------------------------

    async def get_solved_count_by_topic(
        self, student_id: int, topic_ids: list[int]
    ) -> dict[int, int]:
        """Return {topic_id: solved_count} for the student."""
        if not topic_ids:
            return {}
        result = await self.db.execute(
            select(
                CodingChallenge.topic_id,
                func.count(func.distinct(CodingSubmission.challenge_id)),
            )
            .join(
                CodingSubmission,
                and_(
                    CodingSubmission.challenge_id == CodingChallenge.id,
                    CodingSubmission.student_id == student_id,
                    CodingSubmission.status == "passed",
                ),
            )
            .where(CodingChallenge.topic_id.in_(topic_ids))
            .group_by(CodingChallenge.topic_id)
        )
        return {row[0]: row[1] for row in result.all()}

    async def get_student_total_stats(
        self, student_id: int
    ) -> dict:
        """Return aggregate stats: total_solved, total_attempts, total_xp."""
        solved = await self.db.execute(
            select(func.count(func.distinct(CodingSubmission.challenge_id))).where(
                CodingSubmission.student_id == student_id,
                CodingSubmission.status == "passed",
            )
        )
        attempts = await self.db.execute(
            select(func.count(CodingSubmission.id)).where(
                CodingSubmission.student_id == student_id,
            )
        )
        xp = await self.db.execute(
            select(func.coalesce(func.sum(CodingSubmission.xp_earned), 0)).where(
                CodingSubmission.student_id == student_id,
            )
        )
        return {
            "total_solved": solved.scalar() or 0,
            "total_attempts": attempts.scalar() or 0,
            "total_xp": xp.scalar() or 0,
        }


class CourseRepository:
    """Data access for coding courses (learning paths)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # -----------------------------------------------------------------------
    # Courses
    # -----------------------------------------------------------------------

    async def list_courses(self, active_only: bool = True) -> list[CodingCourse]:
        query = select(CodingCourse).order_by(CodingCourse.sort_order)
        if active_only:
            query = query.where(CodingCourse.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_course_by_slug(self, slug: str) -> Optional[CodingCourse]:
        result = await self.db.execute(
            select(CodingCourse).where(CodingCourse.slug == slug)
        )
        return result.scalar_one_or_none()

    async def get_course_by_id(self, course_id: int) -> Optional[CodingCourse]:
        result = await self.db.execute(
            select(CodingCourse).where(CodingCourse.id == course_id)
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Lessons
    # -----------------------------------------------------------------------

    async def list_lessons(
        self, course_id: int, active_only: bool = True
    ) -> list[CodingLesson]:
        query = (
            select(CodingLesson)
            .where(CodingLesson.course_id == course_id)
            .order_by(CodingLesson.sort_order)
        )
        if active_only:
            query = query.where(CodingLesson.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_lesson_by_id(self, lesson_id: int) -> Optional[CodingLesson]:
        result = await self.db.execute(
            select(CodingLesson).where(CodingLesson.id == lesson_id)
        )
        return result.scalar_one_or_none()

    # -----------------------------------------------------------------------
    # Progress
    # -----------------------------------------------------------------------

    async def get_progress(
        self, student_id: int, course_id: int
    ) -> Optional[CodingCourseProgress]:
        result = await self.db.execute(
            select(CodingCourseProgress).where(
                CodingCourseProgress.student_id == student_id,
                CodingCourseProgress.course_id == course_id,
            )
        )
        return result.scalar_one_or_none()

    async def get_all_progress(
        self, student_id: int, course_ids: list[int]
    ) -> dict[int, CodingCourseProgress]:
        """Return {course_id: progress} for the student."""
        if not course_ids:
            return {}
        result = await self.db.execute(
            select(CodingCourseProgress).where(
                CodingCourseProgress.student_id == student_id,
                CodingCourseProgress.course_id.in_(course_ids),
            )
        )
        return {p.course_id: p for p in result.scalars().all()}

    async def upsert_progress(
        self,
        student_id: int,
        course_id: int,
        last_lesson_id: int,
        completed_lessons: int,
        completed_at=None,
    ) -> CodingCourseProgress:
        progress = await self.get_progress(student_id, course_id)
        if progress:
            progress.last_lesson_id = last_lesson_id
            progress.completed_lessons = completed_lessons
            if completed_at:
                progress.completed_at = completed_at
        else:
            progress = CodingCourseProgress(
                student_id=student_id,
                course_id=course_id,
                last_lesson_id=last_lesson_id,
                completed_lessons=completed_lessons,
                completed_at=completed_at,
            )
            self.db.add(progress)
        await self.db.flush()
        await self.db.refresh(progress)
        return progress

    async def get_completed_lesson_ids(
        self, student_id: int, course_id: int
    ) -> set[int]:
        """Return set of lesson IDs that the student has completed.

        A lesson is complete if its sort_order <= progress.completed_lessons - 1.
        We store completed_lessons count, so we retrieve lessons up to that count.
        """
        progress = await self.get_progress(student_id, course_id)
        if not progress or progress.completed_lessons == 0:
            return set()

        result = await self.db.execute(
            select(CodingLesson.id)
            .where(
                CodingLesson.course_id == course_id,
                CodingLesson.is_active == True,
            )
            .order_by(CodingLesson.sort_order)
            .limit(progress.completed_lessons)
        )
        return {row[0] for row in result.all()}
