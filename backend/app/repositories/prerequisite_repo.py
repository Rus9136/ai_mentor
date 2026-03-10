"""
Repository for ParagraphPrerequisite data access.
"""

import logging
from typing import Optional, List, Dict
from collections import defaultdict
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.prerequisite import ParagraphPrerequisite
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.models.textbook import Textbook

logger = logging.getLogger(__name__)


class PrerequisiteRepository:
    """Repository for ParagraphPrerequisite CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, prereq_id: int) -> Optional[ParagraphPrerequisite]:
        """Get a single prerequisite link by ID."""
        result = await self.db.execute(
            select(ParagraphPrerequisite).where(
                ParagraphPrerequisite.id == prereq_id
            )
        )
        return result.scalar_one_or_none()

    async def get_prerequisites(self, paragraph_id: int) -> List[ParagraphPrerequisite]:
        """Get all prerequisites for a paragraph (with prerequisite paragraph loaded)."""
        result = await self.db.execute(
            select(ParagraphPrerequisite)
            .options(
                selectinload(ParagraphPrerequisite.prerequisite)
                .selectinload(Paragraph.chapter)
                .selectinload(Chapter.textbook)
            )
            .where(ParagraphPrerequisite.paragraph_id == paragraph_id)
            .order_by(ParagraphPrerequisite.id)
        )
        return list(result.scalars().all())

    async def get_dependents(self, paragraph_id: int) -> List[ParagraphPrerequisite]:
        """Get all paragraphs that depend on this paragraph."""
        result = await self.db.execute(
            select(ParagraphPrerequisite)
            .options(
                selectinload(ParagraphPrerequisite.paragraph)
                .selectinload(Paragraph.chapter)
            )
            .where(ParagraphPrerequisite.prerequisite_paragraph_id == paragraph_id)
            .order_by(ParagraphPrerequisite.id)
        )
        return list(result.scalars().all())

    async def get_prerequisites_batch(
        self, paragraph_ids: List[int]
    ) -> Dict[int, List[ParagraphPrerequisite]]:
        """
        Batch query: get prerequisites for multiple paragraphs at once.
        Returns Dict[paragraph_id, List[ParagraphPrerequisite]].
        Avoids N+1 when showing paragraph lists.
        """
        if not paragraph_ids:
            return {}

        result = await self.db.execute(
            select(ParagraphPrerequisite)
            .options(
                selectinload(ParagraphPrerequisite.prerequisite)
                .selectinload(Paragraph.chapter)
                .selectinload(Chapter.textbook)
            )
            .where(ParagraphPrerequisite.paragraph_id.in_(paragraph_ids))
        )
        prereqs = result.scalars().all()

        grouped: Dict[int, List[ParagraphPrerequisite]] = defaultdict(list)
        for p in prereqs:
            grouped[p.paragraph_id].append(p)

        return dict(grouped)

    async def get_by_textbook(self, textbook_id: int) -> List[ParagraphPrerequisite]:
        """Get all prerequisite links for a textbook (join through paragraph → chapter)."""
        result = await self.db.execute(
            select(ParagraphPrerequisite)
            .join(Paragraph, ParagraphPrerequisite.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(Chapter.textbook_id == textbook_id)
            .order_by(ParagraphPrerequisite.id)
        )
        return list(result.scalars().all())

    async def exists(
        self, paragraph_id: int, prerequisite_paragraph_id: int
    ) -> bool:
        """Check if a specific prerequisite link already exists."""
        result = await self.db.execute(
            select(ParagraphPrerequisite.id).where(
                ParagraphPrerequisite.paragraph_id == paragraph_id,
                ParagraphPrerequisite.prerequisite_paragraph_id == prerequisite_paragraph_id,
            )
        )
        return result.scalar_one_or_none() is not None

    async def get_all_prerequisites_for_textbook(
        self, textbook_id: int
    ) -> Dict[int, List[int]]:
        """
        Get prerequisite graph as adjacency list for a textbook.
        Returns Dict[paragraph_id, List[prerequisite_paragraph_id]].
        Used for cycle detection.
        """
        result = await self.db.execute(
            select(
                ParagraphPrerequisite.paragraph_id,
                ParagraphPrerequisite.prerequisite_paragraph_id,
            )
            .join(Paragraph, ParagraphPrerequisite.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(Chapter.textbook_id == textbook_id)
        )
        rows = result.fetchall()

        graph: Dict[int, List[int]] = defaultdict(list)
        for row in rows:
            graph[row.paragraph_id].append(row.prerequisite_paragraph_id)

        return dict(graph)

    async def get_all_prerequisites_for_subject(
        self, subject_id: int
    ) -> Dict[int, List[int]]:
        """
        Get prerequisite graph as adjacency list for all textbooks of a subject.
        Returns Dict[paragraph_id, List[prerequisite_paragraph_id]].
        Used for cycle detection across textbooks within the same subject.
        """
        result = await self.db.execute(
            select(
                ParagraphPrerequisite.paragraph_id,
                ParagraphPrerequisite.prerequisite_paragraph_id,
            )
            .join(Paragraph, ParagraphPrerequisite.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .join(Textbook, Chapter.textbook_id == Textbook.id)
            .where(Textbook.subject_id == subject_id)
        )
        rows = result.fetchall()

        graph: Dict[int, List[int]] = defaultdict(list)
        for row in rows:
            graph[row.paragraph_id].append(row.prerequisite_paragraph_id)

        return dict(graph)

    async def create(self, prereq: ParagraphPrerequisite) -> ParagraphPrerequisite:
        """Create a new prerequisite link."""
        self.db.add(prereq)
        await self.db.flush()
        return prereq

    async def delete_by_id(self, prereq_id: int) -> bool:
        """Hard delete a prerequisite link. Returns True if deleted."""
        result = await self.db.execute(
            delete(ParagraphPrerequisite).where(
                ParagraphPrerequisite.id == prereq_id
            )
        )
        await self.db.flush()
        return result.rowcount > 0
