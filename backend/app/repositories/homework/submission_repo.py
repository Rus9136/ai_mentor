"""
Repository for StudentTaskSubmission operations.
"""
from typing import Optional, List, Dict
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import (
    StudentTaskSubmission,
    TaskSubmissionStatus,
)


class SubmissionRepository:
    """Repository for student task submissions."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create_submission(
        self,
        homework_student_id: int,
        task_id: int,
        student_id: int,
        school_id: int,
        attempt_number: int
    ) -> StudentTaskSubmission:
        """Create a task submission."""
        submission = StudentTaskSubmission(
            homework_student_id=homework_student_id,
            homework_task_id=task_id,
            student_id=student_id,
            school_id=school_id,
            attempt_number=attempt_number,
            status=TaskSubmissionStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc)
        )
        self.db.add(submission)
        await self.db.flush()
        await self.db.refresh(submission)
        return submission

    async def get_submission_by_id(
        self,
        submission_id: int,
        load_answers: bool = False
    ) -> Optional[StudentTaskSubmission]:
        """Get submission by ID."""
        query = select(StudentTaskSubmission).where(
            StudentTaskSubmission.id == submission_id,
            StudentTaskSubmission.is_deleted == False
        )

        if load_answers:
            query = query.options(selectinload(StudentTaskSubmission.answers))

        result = await self.db.execute(query)
        return result.unique().scalar_one_or_none()

    async def get_attempts_count(
        self,
        homework_student_id: int,
        task_id: int
    ) -> int:
        """Get number of attempts for a task."""
        result = await self.db.execute(
            select(func.count())
            .select_from(StudentTaskSubmission)
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.homework_task_id == task_id,
                StudentTaskSubmission.is_deleted == False
            )
        )
        return result.scalar() or 0

    async def get_latest_submission(
        self,
        homework_student_id: int,
        task_id: int
    ) -> Optional[StudentTaskSubmission]:
        """Get latest submission for a task."""
        result = await self.db.execute(
            select(StudentTaskSubmission)
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.homework_task_id == task_id,
                StudentTaskSubmission.is_deleted == False
            )
            .order_by(StudentTaskSubmission.attempt_number.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def update_submission(
        self,
        submission_id: int,
        data: dict
    ) -> Optional[StudentTaskSubmission]:
        """Update submission."""
        submission = await self.get_submission_by_id(submission_id)
        if not submission:
            return None

        for key, value in data.items():
            if value is not None:
                setattr(submission, key, value)

        submission.updated_at = datetime.now(timezone.utc)
        await self.db.flush()
        await self.db.refresh(submission)
        return submission

    # =========================================================================
    # Batch methods to avoid N+1 queries
    # =========================================================================

    async def get_attempts_counts_batch(
        self,
        homework_student_id: int,
        task_ids: List[int]
    ) -> Dict[int, int]:
        """
        Get attempt counts for multiple tasks in a single query.

        Returns dict: {task_id: attempts_count}
        """
        if not task_ids:
            return {}

        result = await self.db.execute(
            select(
                StudentTaskSubmission.homework_task_id,
                func.count().label("count")
            )
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.homework_task_id.in_(task_ids),
                StudentTaskSubmission.is_deleted == False
            )
            .group_by(StudentTaskSubmission.homework_task_id)
        )

        counts = {row.homework_task_id: row.count for row in result.all()}
        # Return 0 for tasks without submissions
        return {task_id: counts.get(task_id, 0) for task_id in task_ids}

    async def get_latest_submissions_batch(
        self,
        homework_student_id: int,
        task_ids: List[int]
    ) -> Dict[int, StudentTaskSubmission]:
        """
        Get latest submissions for multiple tasks in a single query.

        Uses window function to get the most recent submission per task.
        Returns dict: {task_id: submission}
        """
        if not task_ids:
            return {}

        from sqlalchemy import and_
        from sqlalchemy.orm import aliased

        # Subquery to get max attempt number per task
        subq = (
            select(
                StudentTaskSubmission.homework_task_id,
                func.max(StudentTaskSubmission.attempt_number).label("max_attempt")
            )
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.homework_task_id.in_(task_ids),
                StudentTaskSubmission.is_deleted == False
            )
            .group_by(StudentTaskSubmission.homework_task_id)
            .subquery()
        )

        # Main query joining with subquery
        result = await self.db.execute(
            select(StudentTaskSubmission)
            .options(selectinload(StudentTaskSubmission.answers))
            .join(
                subq,
                and_(
                    StudentTaskSubmission.homework_task_id == subq.c.homework_task_id,
                    StudentTaskSubmission.attempt_number == subq.c.max_attempt
                )
            )
            .where(
                StudentTaskSubmission.homework_student_id == homework_student_id,
                StudentTaskSubmission.is_deleted == False
            )
        )

        submissions = result.unique().scalars().all()
        return {sub.homework_task_id: sub for sub in submissions}
