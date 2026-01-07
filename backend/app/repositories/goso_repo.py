"""
Repository for GOSO (State Educational Standard) data access.
"""
from typing import Optional, List, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.subject import Subject
from app.models.goso import (
    Framework,
    GosoSection,
    GosoSubsection,
    LearningOutcome,
    ParagraphOutcome,
)


class GosoRepository:
    """Repository for GOSO data access (read-only operations)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ==================== Subject ====================

    async def get_all_subjects(self, is_active: bool = True) -> List[Subject]:
        """
        Get all subjects.

        Args:
            is_active: Filter by active status

        Returns:
            List of subjects
        """
        query = select(Subject)
        if is_active:
            query = query.where(Subject.is_active == True)
        query = query.order_by(Subject.name_ru)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_subject_by_id(self, subject_id: int) -> Optional[Subject]:
        """
        Get subject by ID.

        Args:
            subject_id: Subject ID

        Returns:
            Subject or None
        """
        result = await self.db.execute(
            select(Subject).where(Subject.id == subject_id)
        )
        return result.scalar_one_or_none()

    async def get_subject_by_code(self, code: str) -> Optional[Subject]:
        """
        Get subject by code.

        Args:
            code: Subject code (e.g., 'history_kz')

        Returns:
            Subject or None
        """
        result = await self.db.execute(
            select(Subject).where(Subject.code == code)
        )
        return result.scalar_one_or_none()

    # ==================== Framework ====================

    async def get_all_frameworks(
        self,
        subject_id: Optional[int] = None,
        is_active: bool = True
    ) -> List[Framework]:
        """
        Get all frameworks (GOSO versions).

        Args:
            subject_id: Filter by subject
            is_active: Filter by active status

        Returns:
            List of frameworks
        """
        query = select(Framework).where(Framework.is_deleted == False)

        if subject_id is not None:
            query = query.where(Framework.subject_id == subject_id)
        if is_active:
            query = query.where(Framework.is_active == True)

        query = query.order_by(Framework.order_date.desc())

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_framework_by_id(
        self,
        framework_id: int,
        load_structure: bool = False
    ) -> Optional[Framework]:
        """
        Get framework by ID.

        Args:
            framework_id: Framework ID
            load_structure: Whether to eager load sections

        Returns:
            Framework or None
        """
        query = select(Framework).where(
            Framework.id == framework_id,
            Framework.is_deleted == False
        )

        if load_structure:
            query = query.options(
                selectinload(Framework.sections)
                .selectinload(GosoSection.subsections)
                .selectinload(GosoSubsection.outcomes)
            )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== GosoSection ====================

    async def get_sections_by_framework(
        self,
        framework_id: int,
        is_active: bool = True,
        load_full_structure: bool = False
    ) -> List[GosoSection]:
        """
        Get sections by framework.

        Args:
            framework_id: Framework ID
            is_active: Filter by active status
            load_full_structure: Load subsections and outcomes

        Returns:
            List of sections
        """
        query = select(GosoSection).where(GosoSection.framework_id == framework_id)

        if is_active:
            query = query.where(GosoSection.is_active == True)

        if load_full_structure:
            query = query.options(
                selectinload(GosoSection.subsections)
                .selectinload(GosoSubsection.outcomes)
            )

        query = query.order_by(GosoSection.display_order)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_section_by_id(
        self,
        section_id: int,
        load_subsections: bool = False
    ) -> Optional[GosoSection]:
        """
        Get section by ID.

        Args:
            section_id: Section ID
            load_subsections: Whether to eager load subsections

        Returns:
            GosoSection or None
        """
        query = select(GosoSection).where(GosoSection.id == section_id)

        if load_subsections:
            query = query.options(selectinload(GosoSection.subsections))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== GosoSubsection ====================

    async def get_subsections_by_section(
        self,
        section_id: int,
        is_active: bool = True
    ) -> List[GosoSubsection]:
        """
        Get subsections by section.

        Args:
            section_id: Section ID
            is_active: Filter by active status

        Returns:
            List of subsections
        """
        query = select(GosoSubsection).where(GosoSubsection.section_id == section_id)

        if is_active:
            query = query.where(GosoSubsection.is_active == True)

        query = query.order_by(GosoSubsection.display_order)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_subsection_by_id(
        self,
        subsection_id: int,
        load_outcomes: bool = False
    ) -> Optional[GosoSubsection]:
        """
        Get subsection by ID.

        Args:
            subsection_id: Subsection ID
            load_outcomes: Whether to eager load outcomes

        Returns:
            GosoSubsection or None
        """
        query = select(GosoSubsection).where(GosoSubsection.id == subsection_id)

        if load_outcomes:
            query = query.options(selectinload(GosoSubsection.outcomes))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    # ==================== LearningOutcome ====================

    async def get_outcomes(
        self,
        framework_id: Optional[int] = None,
        grade: Optional[int] = None,
        subsection_id: Optional[int] = None,
        section_id: Optional[int] = None,
        is_active: bool = True,
        limit: int = 100,
        offset: int = 0
    ) -> List[LearningOutcome]:
        """
        Get learning outcomes with filters.

        Args:
            framework_id: Filter by framework
            grade: Filter by grade level (5-11)
            subsection_id: Filter by subsection
            section_id: Filter by section (requires join)
            is_active: Filter by active status
            limit: Limit results
            offset: Offset for pagination

        Returns:
            List of learning outcomes
        """
        query = select(LearningOutcome).where(LearningOutcome.is_deleted == False)

        if framework_id is not None:
            query = query.where(LearningOutcome.framework_id == framework_id)
        if grade is not None:
            query = query.where(LearningOutcome.grade == grade)
        if subsection_id is not None:
            query = query.where(LearningOutcome.subsection_id == subsection_id)
        if section_id is not None:
            # Need to join with subsections to filter by section
            query = query.join(GosoSubsection).where(GosoSubsection.section_id == section_id)
        if is_active:
            query = query.where(LearningOutcome.is_active == True)

        query = query.order_by(
            LearningOutcome.grade,
            LearningOutcome.display_order,
            LearningOutcome.code
        ).limit(limit).offset(offset)

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_outcome_by_id(self, outcome_id: int) -> Optional[LearningOutcome]:
        """
        Get outcome by ID.

        Args:
            outcome_id: Outcome ID

        Returns:
            LearningOutcome or None
        """
        result = await self.db.execute(
            select(LearningOutcome).where(
                LearningOutcome.id == outcome_id,
                LearningOutcome.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def get_outcome_with_context(self, outcome_id: int) -> Optional[dict]:
        """
        Get outcome with section/subsection context.

        Args:
            outcome_id: Outcome ID

        Returns:
            Dict with outcome and context or None
        """
        query = (
            select(LearningOutcome)
            .where(
                LearningOutcome.id == outcome_id,
                LearningOutcome.is_deleted == False
            )
            .options(
                selectinload(LearningOutcome.subsection).selectinload(GosoSubsection.section)
            )
        )

        result = await self.db.execute(query)
        outcome = result.scalar_one_or_none()

        if not outcome:
            return None

        # Build context dict
        context = {
            "outcome": outcome,
            "section_code": None,
            "section_name_ru": None,
            "subsection_code": None,
            "subsection_name_ru": None,
        }

        if outcome.subsection:
            context["subsection_code"] = outcome.subsection.code
            context["subsection_name_ru"] = outcome.subsection.name_ru

            if outcome.subsection.section:
                context["section_code"] = outcome.subsection.section.code
                context["section_name_ru"] = outcome.subsection.section.name_ru

        return context


class ParagraphOutcomeRepository:
    """Repository for paragraph-outcome mapping CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, paragraph_outcome: ParagraphOutcome) -> ParagraphOutcome:
        """
        Create a new paragraph-outcome link.

        Args:
            paragraph_outcome: ParagraphOutcome instance

        Returns:
            Created ParagraphOutcome
        """
        self.db.add(paragraph_outcome)
        await self.db.commit()
        await self.db.refresh(paragraph_outcome)
        return paragraph_outcome

    async def get_by_id(self, id: int) -> Optional[ParagraphOutcome]:
        """
        Get paragraph-outcome link by ID.

        Args:
            id: ParagraphOutcome ID

        Returns:
            ParagraphOutcome or None
        """
        result = await self.db.execute(
            select(ParagraphOutcome).where(ParagraphOutcome.id == id)
        )
        return result.scalar_one_or_none()

    async def get_by_paragraph(
        self,
        paragraph_id: int,
        load_outcome: bool = False
    ) -> List[ParagraphOutcome]:
        """
        Get all outcomes for a paragraph.

        Args:
            paragraph_id: Paragraph ID
            load_outcome: Whether to eager load outcome details

        Returns:
            List of ParagraphOutcome links
        """
        query = select(ParagraphOutcome).where(
            ParagraphOutcome.paragraph_id == paragraph_id
        )

        if load_outcome:
            query = query.options(
                selectinload(ParagraphOutcome.outcome).selectinload(
                    LearningOutcome.subsection
                ).selectinload(GosoSubsection.section)
            )

        result = await self.db.execute(query)
        return result.scalars().all()

    async def get_by_paragraph_paginated(
        self,
        paragraph_id: int,
        page: int = 1,
        page_size: int = 20,
        load_outcome: bool = False
    ) -> Tuple[List[ParagraphOutcome], int]:
        """
        Get all outcomes for a paragraph with pagination.

        Args:
            paragraph_id: Paragraph ID
            page: Page number (1-indexed)
            page_size: Number of items per page
            load_outcome: Whether to eager load outcome details

        Returns:
            Tuple of (list of paragraph outcomes, total count)
        """
        # Base query
        query = select(ParagraphOutcome).where(
            ParagraphOutcome.paragraph_id == paragraph_id
        )

        # Count total before pagination
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply eager loading
        if load_outcome:
            query = query.options(
                selectinload(ParagraphOutcome.outcome).selectinload(
                    LearningOutcome.subsection
                ).selectinload(GosoSubsection.section)
            )

        # Apply ordering and pagination
        query = query.order_by(ParagraphOutcome.id)
        offset = (page - 1) * page_size
        query = query.offset(offset).limit(page_size)

        result = await self.db.execute(query)
        outcomes = list(result.scalars().all())

        return outcomes, total

    async def get_by_outcome(self, outcome_id: int) -> List[ParagraphOutcome]:
        """
        Get all paragraphs for an outcome.

        Args:
            outcome_id: Outcome ID

        Returns:
            List of ParagraphOutcome links
        """
        result = await self.db.execute(
            select(ParagraphOutcome).where(ParagraphOutcome.outcome_id == outcome_id)
        )
        return result.scalars().all()

    async def get_by_paragraph_and_outcome(
        self,
        paragraph_id: int,
        outcome_id: int
    ) -> Optional[ParagraphOutcome]:
        """
        Get specific paragraph-outcome link.

        Args:
            paragraph_id: Paragraph ID
            outcome_id: Outcome ID

        Returns:
            ParagraphOutcome or None
        """
        result = await self.db.execute(
            select(ParagraphOutcome).where(
                ParagraphOutcome.paragraph_id == paragraph_id,
                ParagraphOutcome.outcome_id == outcome_id
            )
        )
        return result.scalar_one_or_none()

    async def update(self, paragraph_outcome: ParagraphOutcome) -> ParagraphOutcome:
        """
        Update a paragraph-outcome link.

        Args:
            paragraph_outcome: ParagraphOutcome instance with updated fields

        Returns:
            Updated ParagraphOutcome
        """
        await self.db.commit()
        await self.db.refresh(paragraph_outcome)
        return paragraph_outcome

    async def delete(self, paragraph_outcome: ParagraphOutcome) -> None:
        """
        Delete a paragraph-outcome link (hard delete).

        Args:
            paragraph_outcome: ParagraphOutcome instance to delete
        """
        await self.db.delete(paragraph_outcome)
        await self.db.commit()
