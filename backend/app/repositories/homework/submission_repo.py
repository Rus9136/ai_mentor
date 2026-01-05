"""
Repository for StudentTaskSubmission operations.
"""
from typing import Optional
from datetime import datetime
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
            started_at=datetime.utcnow()
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

        submission.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(submission)
        return submission
