"""
Repository for Test data access.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, and_, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload, joinedload

from app.models.test import Test, Question, QuestionOption, TestPurpose


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

        # Use selectinload for better compatibility with async drivers
        # selectinload makes separate queries but avoids JOIN issues with psycopg/asyncpg
        if load_questions:
            query = query.options(
                selectinload(Test.questions).selectinload(Question.options)
            )

        result = await self.db.execute(query)
        test = result.unique().scalar_one_or_none()

        # Sort questions and options by sort_order (joinedload doesn't respect order_by in relationships)
        if test and load_questions and test.questions:
            test.questions.sort(key=lambda q: q.sort_order)
            for question in test.questions:
                if question.options:
                    question.options.sort(key=lambda o: o.sort_order)

        return test

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

    async def get_available_for_student(
        self,
        school_id: int,
        chapter_id: Optional[int] = None,
        paragraph_id: Optional[int] = None,
        test_purpose: Optional[TestPurpose] = None,
        is_active_only: bool = True
    ) -> List[Test]:
        """
        Get tests available for a student.

        Returns both global tests (school_id = NULL) and school-specific tests.

        Args:
            school_id: School ID
            chapter_id: Filter by chapter (optional)
            paragraph_id: Filter by paragraph (optional)
            test_purpose: Filter by test purpose (optional)
            is_active_only: Only return active tests (default True)

        Returns:
            List of available tests
        """
        filters = [
            (Test.school_id == school_id) | (Test.school_id.is_(None)),
            Test.is_deleted == False
        ]

        if is_active_only:
            filters.append(Test.is_active == True)

        if chapter_id is not None:
            filters.append(Test.chapter_id == chapter_id)

        if paragraph_id is not None:
            filters.append(Test.paragraph_id == paragraph_id)

        if test_purpose is not None:
            filters.append(Test.test_purpose == test_purpose)

        result = await self.db.execute(
            select(Test).where(
                and_(*filters)
            ).options(
                selectinload(Test.questions)
            ).order_by(Test.difficulty, Test.title)
        )
        return result.scalars().all()

    async def get_by_paragraph(
        self,
        paragraph_id: int,
        school_id: int
    ) -> List[Test]:
        """
        Get tests for a specific paragraph.

        Returns both global and school-specific tests.

        Args:
            paragraph_id: Paragraph ID
            school_id: School ID

        Returns:
            List of tests
        """
        result = await self.db.execute(
            select(Test).where(
                Test.paragraph_id == paragraph_id,
                (Test.school_id == school_id) | (Test.school_id.is_(None)),
                Test.is_deleted == False
            ).order_by(Test.difficulty, Test.title)
        )
        return result.scalars().all()

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
