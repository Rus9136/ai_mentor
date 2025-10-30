"""
Repository for Paragraph data access.
"""
from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.paragraph import Paragraph


class ParagraphRepository:
    """Repository for Paragraph CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, paragraph_id: int) -> Optional[Paragraph]:
        """
        Get paragraph by ID.

        Args:
            paragraph_id: Paragraph ID

        Returns:
            Paragraph or None if not found
        """
        result = await self.db.execute(
            select(Paragraph).where(
                Paragraph.id == paragraph_id,
                Paragraph.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_chapter(self, chapter_id: int) -> List[Paragraph]:
        """
        Get all paragraphs for a chapter.

        Args:
            chapter_id: Chapter ID

        Returns:
            List of paragraphs ordered by order field
        """
        result = await self.db.execute(
            select(Paragraph).where(
                Paragraph.chapter_id == chapter_id,
                Paragraph.is_deleted == False
            ).order_by(Paragraph.order)
        )
        return result.scalars().all()

    async def create(self, paragraph: Paragraph) -> Paragraph:
        """
        Create a new paragraph.

        Args:
            paragraph: Paragraph instance

        Returns:
            Created paragraph
        """
        self.db.add(paragraph)
        await self.db.commit()
        await self.db.refresh(paragraph)
        return paragraph

    async def update(self, paragraph: Paragraph) -> Paragraph:
        """
        Update an existing paragraph.

        Args:
            paragraph: Paragraph instance with updated fields

        Returns:
            Updated paragraph
        """
        await self.db.commit()
        await self.db.refresh(paragraph)
        return paragraph

    async def soft_delete(self, paragraph: Paragraph) -> Paragraph:
        """
        Soft delete a paragraph.

        Args:
            paragraph: Paragraph instance

        Returns:
            Deleted paragraph
        """
        from datetime import datetime
        paragraph.is_deleted = True
        paragraph.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(paragraph)
        return paragraph
