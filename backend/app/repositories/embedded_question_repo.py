"""
Repository for EmbeddedQuestion data access.
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.embedded_question import EmbeddedQuestion


class EmbeddedQuestionRepository:
    """Repository for EmbeddedQuestion CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, question_id: int) -> Optional[EmbeddedQuestion]:
        """Get embedded question by ID (active only)."""
        result = await self.db.execute(
            select(EmbeddedQuestion).where(
                EmbeddedQuestion.id == question_id,
                EmbeddedQuestion.is_active == True  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def get_by_paragraph(self, paragraph_id: int) -> List[EmbeddedQuestion]:
        """Get all active embedded questions for a paragraph, ordered by sort_order."""
        result = await self.db.execute(
            select(EmbeddedQuestion).where(
                EmbeddedQuestion.paragraph_id == paragraph_id,
                EmbeddedQuestion.is_active == True  # noqa: E712
            ).order_by(EmbeddedQuestion.sort_order)
        )
        return result.scalars().all()

    async def create(self, question: EmbeddedQuestion) -> EmbeddedQuestion:
        """Create a new embedded question."""
        self.db.add(question)
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def update(self, question: EmbeddedQuestion) -> EmbeddedQuestion:
        """Update an existing embedded question."""
        await self.db.commit()
        await self.db.refresh(question)
        return question

    async def soft_delete(self, question: EmbeddedQuestion) -> EmbeddedQuestion:
        """Soft delete an embedded question (set is_active=False)."""
        question.is_active = False
        await self.db.commit()
        await self.db.refresh(question)
        return question
