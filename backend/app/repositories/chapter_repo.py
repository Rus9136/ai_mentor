"""
Repository for Chapter data access.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter


class ChapterRepository:
    """Repository for Chapter CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, chapter_id: int) -> Optional[Chapter]:
        """
        Get chapter by ID.

        Args:
            chapter_id: Chapter ID

        Returns:
            Chapter or None if not found
        """
        result = await self.db.execute(
            select(Chapter).where(
                Chapter.id == chapter_id,
                Chapter.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_by_textbook(self, textbook_id: int) -> List[Chapter]:
        """
        Get all chapters for a textbook.

        Args:
            textbook_id: Textbook ID

        Returns:
            List of chapters ordered by order field
        """
        result = await self.db.execute(
            select(Chapter).where(
                Chapter.textbook_id == textbook_id,
                Chapter.is_deleted == False
            ).order_by(Chapter.order)
        )
        return result.scalars().all()

    async def get_by_textbook_paginated(
        self,
        textbook_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[Chapter], int]:
        """
        Get all chapters for a textbook with pagination.

        Args:
            textbook_id: Textbook ID
            page: Page number (1-indexed)
            page_size: Number of items per page

        Returns:
            Tuple of (list of chapters, total count)
        """
        # Base query
        query = select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.is_deleted == False  # noqa: E712
        )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering and pagination
        query = query.order_by(Chapter.order)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        chapters = list(result.scalars().all())

        return chapters, total

    async def create(self, chapter: Chapter) -> Chapter:
        """
        Create a new chapter.

        Args:
            chapter: Chapter instance

        Returns:
            Created chapter
        """
        self.db.add(chapter)
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter

    async def update(self, chapter: Chapter) -> Chapter:
        """
        Update an existing chapter.

        Args:
            chapter: Chapter instance with updated fields

        Returns:
            Updated chapter
        """
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter

    async def soft_delete(self, chapter: Chapter) -> Chapter:
        """
        Soft delete a chapter.

        Args:
            chapter: Chapter instance

        Returns:
            Deleted chapter
        """
        from datetime import datetime
        chapter.is_deleted = True
        chapter.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(chapter)
        return chapter
