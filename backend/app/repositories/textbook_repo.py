"""
Repository for Textbook data access.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, or_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.subject import Subject


class TextbookRepository:
    """Repository for Textbook CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        textbook_id: int,
        load_chapters: bool = False,
        load_subject: bool = True
    ) -> Optional[Textbook]:
        """
        Get textbook by ID.

        Args:
            textbook_id: Textbook ID
            load_chapters: Whether to eager load chapters
            load_subject: Whether to eager load subject (default True)

        Returns:
            Textbook or None if not found
        """
        query = select(Textbook).where(
            Textbook.id == textbook_id,
            Textbook.is_deleted == False
        )

        if load_subject:
            query = query.options(selectinload(Textbook.subject_rel))

        if load_chapters:
            query = query.options(selectinload(Textbook.chapters))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_all_global(self) -> List[Textbook]:
        """
        Get all global textbooks (school_id = NULL).

        Returns:
            List of global textbooks
        """
        result = await self.db.execute(
            select(Textbook)
            .options(selectinload(Textbook.subject_rel))
            .where(
                Textbook.school_id.is_(None),
                Textbook.is_deleted == False
            ).order_by(Textbook.grade_level, Textbook.subject, Textbook.title)
        )
        return result.scalars().all()

    async def get_by_school(
        self,
        school_id: int,
        include_global: bool = False
    ) -> List[Textbook]:
        """
        Get textbooks for a specific school.

        Args:
            school_id: School ID
            include_global: Whether to include global textbooks

        Returns:
            List of textbooks
        """
        if include_global:
            # Get both school-specific and global textbooks
            result = await self.db.execute(
                select(Textbook)
                .options(selectinload(Textbook.subject_rel))
                .where(
                    (Textbook.school_id == school_id) | (Textbook.school_id.is_(None)),
                    Textbook.is_deleted == False
                ).order_by(Textbook.grade_level, Textbook.subject, Textbook.title)
            )
        else:
            # Only school-specific textbooks
            result = await self.db.execute(
                select(Textbook)
                .options(selectinload(Textbook.subject_rel))
                .where(
                    Textbook.school_id == school_id,
                    Textbook.is_deleted == False
                ).order_by(Textbook.grade_level, Textbook.subject, Textbook.title)
            )

        return result.scalars().all()

    async def get_by_school_paginated(
        self,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        include_global: bool = False,
        load_subject: bool = True,
    ) -> Tuple[List[Textbook], int]:
        """
        Get textbooks for a school with pagination.

        Args:
            school_id: School ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            include_global: Whether to include global textbooks
            load_subject: Whether to eager load subject

        Returns:
            Tuple of (list of textbooks, total count)
        """
        # Build filters
        if include_global:
            filter_condition = or_(
                Textbook.school_id == school_id,
                Textbook.school_id.is_(None)
            )
        else:
            filter_condition = Textbook.school_id == school_id

        # Base query
        query = select(Textbook).where(
            filter_condition,
            Textbook.is_deleted == False  # noqa: E712
        )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply ordering
        query = query.order_by(Textbook.grade_level, Textbook.subject, Textbook.title)

        # Apply eager loading
        if load_subject:
            query = query.options(selectinload(Textbook.subject_rel))

        # Apply pagination
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        textbooks = list(result.scalars().all())

        return textbooks, total

    async def create(self, textbook: Textbook) -> Textbook:
        """
        Create a new textbook.

        Args:
            textbook: Textbook instance

        Returns:
            Created textbook
        """
        self.db.add(textbook)
        await self.db.commit()
        await self.db.refresh(textbook)
        return textbook

    async def update(self, textbook: Textbook) -> Textbook:
        """
        Update an existing textbook.

        Args:
            textbook: Textbook instance with updated fields

        Returns:
            Updated textbook
        """
        await self.db.commit()
        await self.db.refresh(textbook)
        return textbook

    async def soft_delete(self, textbook: Textbook) -> Textbook:
        """
        Soft delete a textbook.

        Args:
            textbook: Textbook instance

        Returns:
            Deleted textbook
        """
        from datetime import datetime
        textbook.is_deleted = True
        textbook.deleted_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(textbook)
        return textbook

    async def fork_textbook(
        self,
        source_textbook: Textbook,
        target_school_id: int
    ) -> Textbook:
        """
        Fork (customize) a global textbook for a specific school.
        Creates a complete copy of the textbook with all chapters and paragraphs.

        Args:
            source_textbook: Source global textbook to fork
            target_school_id: Target school ID

        Returns:
            Forked textbook with all chapters and paragraphs
        """
        # Load chapters and paragraphs
        result = await self.db.execute(
            select(Textbook)
            .where(Textbook.id == source_textbook.id)
            .options(
                selectinload(Textbook.chapters).selectinload(Chapter.paragraphs)
            )
        )
        source_with_children = result.scalar_one()

        # Create forked textbook
        forked_textbook = Textbook(
            school_id=target_school_id,
            global_textbook_id=source_textbook.id,
            is_customized=True,
            version=1,  # New fork starts at version 1
            source_version=source_textbook.version,  # Track source version
            title=f"{source_textbook.title} (Customized)",
            subject_id=source_textbook.subject_id,  # Copy subject FK
            subject=source_textbook.subject,  # Copy text for backward compat
            grade_level=source_textbook.grade_level,
            author=source_textbook.author,
            publisher=source_textbook.publisher,
            year=source_textbook.year,
            isbn=source_textbook.isbn,
            description=source_textbook.description,
            is_active=source_textbook.is_active,
        )

        self.db.add(forked_textbook)
        await self.db.flush()  # Get textbook ID without committing

        # Copy chapters
        for source_chapter in source_with_children.chapters:
            if source_chapter.is_deleted:
                continue

            forked_chapter = Chapter(
                textbook_id=forked_textbook.id,
                title=source_chapter.title,
                number=source_chapter.number,
                order=source_chapter.order,
                description=source_chapter.description,
                learning_objective=source_chapter.learning_objective,
            )

            self.db.add(forked_chapter)
            await self.db.flush()  # Get chapter ID

            # Copy paragraphs
            for source_paragraph in source_chapter.paragraphs:
                if source_paragraph.is_deleted:
                    continue

                forked_paragraph = Paragraph(
                    chapter_id=forked_chapter.id,
                    title=source_paragraph.title,
                    number=source_paragraph.number,
                    order=source_paragraph.order,
                    content=source_paragraph.content,
                    summary=source_paragraph.summary,
                    learning_objective=source_paragraph.learning_objective,
                    lesson_objective=source_paragraph.lesson_objective,
                    key_terms=source_paragraph.key_terms,
                    questions=source_paragraph.questions,
                )

                self.db.add(forked_paragraph)

        await self.db.commit()
        await self.db.refresh(forked_textbook)

        return forked_textbook
