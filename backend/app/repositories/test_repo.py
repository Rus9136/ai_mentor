"""
Repository for Test data access.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test import Test, Question


class TestRepository:
    """Repository for Test CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        test_id: int,
        load_questions: bool = False
    ) -> Optional[Test]:
        """
        Get test by ID.

        Args:
            test_id: Test ID
            load_questions: Whether to eager load questions with options

        Returns:
            Test or None if not found
        """
        query = select(Test).where(
            Test.id == test_id,
            Test.is_deleted == False
        )

        if load_questions:
            query = query.options(
                selectinload(Test.questions).selectinload(Question.options)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_global(self) -> List[Test]:
        """
        Get all global tests (school_id = NULL).

        Returns:
            List of global tests
        """
        result = await self.db.execute(
            select(Test).where(
                Test.school_id.is_(None),
                Test.is_deleted == False
            ).order_by(Test.difficulty, Test.title)
        )
        return result.scalars().all()

    async def get_by_school(
        self,
        school_id: int,
        include_global: bool = False
    ) -> List[Test]:
        """
        Get tests for a specific school.

        Args:
            school_id: School ID
            include_global: Whether to include global tests

        Returns:
            List of tests
        """
        if include_global:
            # Get both school-specific and global tests
            result = await self.db.execute(
                select(Test).where(
                    (Test.school_id == school_id) | (Test.school_id.is_(None)),
                    Test.is_deleted == False
                ).order_by(Test.difficulty, Test.title)
            )
        else:
            # Only school-specific tests
            result = await self.db.execute(
                select(Test).where(
                    Test.school_id == school_id,
                    Test.is_deleted == False
                ).order_by(Test.difficulty, Test.title)
            )

        return result.scalars().all()

    async def get_by_chapter(
        self,
        chapter_id: int,
        school_id: Optional[int] = None
    ) -> List[Test]:
        """
        Get tests for a specific chapter.

        Args:
            chapter_id: Chapter ID
            school_id: School ID (if provided, includes both school and global tests)

        Returns:
            List of tests
        """
        if school_id is not None:
            # Get both school-specific and global tests for this chapter
            result = await self.db.execute(
                select(Test).where(
                    Test.chapter_id == chapter_id,
                    (Test.school_id == school_id) | (Test.school_id.is_(None)),
                    Test.is_deleted == False
                ).order_by(Test.difficulty, Test.title)
            )
        else:
            # Get all tests for this chapter (including global only)
            result = await self.db.execute(
                select(Test).where(
                    Test.chapter_id == chapter_id,
                    Test.is_deleted == False
                ).order_by(Test.difficulty, Test.title)
            )

        return result.scalars().all()

    async def create(self, test: Test) -> Test:
        """
        Create a new test.

        Args:
            test: Test instance

        Returns:
            Created test
        """
        self.db.add(test)
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def update(self, test: Test) -> Test:
        """
        Update an existing test.

        Args:
            test: Test instance with updated fields

        Returns:
            Updated test
        """
        await self.db.commit()
        await self.db.refresh(test)
        return test

    async def soft_delete(self, test: Test) -> Test:
        """
        Soft delete a test.

        Args:
            test: Test instance

        Returns:
            Deleted test
        """
        test.is_deleted = True
        test.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(test)
        return test
