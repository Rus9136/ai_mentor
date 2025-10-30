"""
Repository for Question and QuestionOption data access.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test import Question, QuestionOption


class QuestionRepository:
    """Repository for Question CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        question_id: int,
        load_options: bool = True
    ) -> Optional[Question]:
        """
        Get question by ID.

        Args:
            question_id: Question ID
            load_options: Whether to eager load options

        Returns:
            Question or None if not found
        """
        query = select(Question).where(
            Question.id == question_id,
            Question.is_deleted == False
        )

        if load_options:
            query = query.options(selectinload(Question.options))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_by_test(self, test_id: int) -> List[Question]:
        """
        Get all questions for a specific test.

        Args:
            test_id: Test ID

        Returns:
            List of questions with options, ordered by question.order
        """
        result = await self.db.execute(
            select(Question)
            .where(
                Question.test_id == test_id,
                Question.is_deleted == False
            )
            .options(selectinload(Question.options))
            .order_by(Question.order)
        )
        return result.scalars().all()

    async def create(self, question: Question) -> Question:
        """
        Create a new question.

        Args:
            question: Question instance

        Returns:
            Created question
        """
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def update(self, question: Question) -> Question:
        """
        Update an existing question.

        Args:
            question: Question instance with updated fields

        Returns:
            Updated question
        """
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def soft_delete(self, question: Question) -> Question:
        """
        Soft delete a question (cascade deletes options).

        Args:
            question: Question instance

        Returns:
            Deleted question
        """
        question.is_deleted = True
        question.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(question)
        return question


class QuestionOptionRepository:
    """Repository for QuestionOption CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, option_id: int) -> Optional[QuestionOption]:
        """
        Get question option by ID.

        Args:
            option_id: QuestionOption ID

        Returns:
            QuestionOption or None if not found
        """
        result = await self.db.execute(
            select(QuestionOption).where(
                QuestionOption.id == option_id,
                QuestionOption.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_question(self, question_id: int) -> List[QuestionOption]:
        """
        Get all options for a specific question.

        Args:
            question_id: Question ID

        Returns:
            List of options, ordered by option.order
        """
        result = await self.db.execute(
            select(QuestionOption)
            .where(
                QuestionOption.question_id == question_id,
                QuestionOption.is_deleted == False
            )
            .order_by(QuestionOption.order)
        )
        return result.scalars().all()

    async def create(self, option: QuestionOption) -> QuestionOption:
        """
        Create a new question option.

        Args:
            option: QuestionOption instance

        Returns:
            Created option
        """
        self.db.add(option)
        await self.db.commit()
        await self.db.refresh(option)
        return option

    async def update(self, option: QuestionOption) -> QuestionOption:
        """
        Update an existing question option.

        Args:
            option: QuestionOption instance with updated fields

        Returns:
            Updated option
        """
        await self.db.commit()
        await self.db.refresh(option)
        return option

    async def soft_delete(self, option: QuestionOption) -> QuestionOption:
        """
        Soft delete a question option.

        Args:
            option: QuestionOption instance

        Returns:
            Deleted option
        """
        option.is_deleted = True
        option.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(option)
        return option
