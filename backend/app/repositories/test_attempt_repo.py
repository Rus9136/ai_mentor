"""
Repository for TestAttempt data access.
"""
from typing import Optional, List
from sqlalchemy import select, func, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test_attempt import TestAttempt, TestAttemptAnswer
from app.models.test import Question


class TestAttemptRepository:
    """Repository for TestAttempt CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        attempt_id: int,
        student_id: int,
        school_id: int
    ) -> Optional[TestAttempt]:
        """
        Get test attempt by ID with ownership and tenant isolation.

        Args:
            attempt_id: Test attempt ID
            student_id: Student ID (ownership check)
            school_id: School ID (tenant isolation)

        Returns:
            TestAttempt or None if not found or access denied
        """
        result = await self.db.execute(
            select(TestAttempt).where(
                TestAttempt.id == attempt_id,
                TestAttempt.student_id == student_id,
                TestAttempt.school_id == school_id
            )
        )
        return result.scalar_one_or_none()

    async def get_student_attempts(
        self,
        student_id: int,
        test_id: int,
        school_id: int
    ) -> List[TestAttempt]:
        """
        Get all attempts for a specific student and test.

        Args:
            student_id: Student ID
            test_id: Test ID
            school_id: School ID (tenant isolation)

        Returns:
            List of test attempts sorted by attempt_number DESC
        """
        result = await self.db.execute(
            select(TestAttempt).where(
                TestAttempt.student_id == student_id,
                TestAttempt.test_id == test_id,
                TestAttempt.school_id == school_id
            ).order_by(desc(TestAttempt.attempt_number))
        )
        return result.scalars().all()

    async def get_latest_attempt(
        self,
        student_id: int,
        test_id: int
    ) -> Optional[TestAttempt]:
        """
        Get the most recent attempt for a student and test.

        Args:
            student_id: Student ID
            test_id: Test ID

        Returns:
            Latest TestAttempt or None if no attempts exist
        """
        result = await self.db.execute(
            select(TestAttempt).where(
                TestAttempt.student_id == student_id,
                TestAttempt.test_id == test_id
            ).order_by(desc(TestAttempt.attempt_number)).limit(1)
        )
        return result.scalar_one_or_none()

    async def count_attempts(
        self,
        student_id: int,
        test_id: int
    ) -> int:
        """
        Count how many attempts a student has made for a test.

        Args:
            student_id: Student ID
            test_id: Test ID

        Returns:
            Number of attempts
        """
        result = await self.db.execute(
            select(func.count(TestAttempt.id)).where(
                TestAttempt.student_id == student_id,
                TestAttempt.test_id == test_id
            )
        )
        return result.scalar() or 0

    async def create(self, attempt: TestAttempt) -> TestAttempt:
        """
        Create a new test attempt.

        Args:
            attempt: TestAttempt instance

        Returns:
            Created test attempt
        """
        self.db.add(attempt)
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def update(self, attempt: TestAttempt) -> TestAttempt:
        """
        Update an existing test attempt.

        Args:
            attempt: TestAttempt instance with updated fields

        Returns:
            Updated test attempt
        """
        await self.db.commit()
        await self.db.refresh(attempt)
        return attempt

    async def get_with_answers(
        self,
        attempt_id: int
    ) -> Optional[TestAttempt]:
        """
        Get test attempt with eager-loaded answers and questions.

        This is useful for displaying attempt results with all answer details.

        Args:
            attempt_id: Test attempt ID

        Returns:
            TestAttempt with answers and questions, or None if not found
        """
        result = await self.db.execute(
            select(TestAttempt).where(
                TestAttempt.id == attempt_id
            ).options(
                selectinload(TestAttempt.answers).selectinload(TestAttemptAnswer.question)
            )
        )
        return result.scalar_one_or_none()
