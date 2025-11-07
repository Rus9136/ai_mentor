"""
Repository for ParagraphMastery data access.
"""
from typing import Optional, List, Dict
from datetime import datetime
from sqlalchemy import select, func, case
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.mastery import ParagraphMastery
from app.models.paragraph import Paragraph


class ParagraphMasteryRepository:
    """Repository for ParagraphMastery CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_student_paragraph(
        self,
        student_id: int,
        paragraph_id: int
    ) -> Optional[ParagraphMastery]:
        """
        Get paragraph mastery record for a specific student and paragraph.

        Args:
            student_id: Student ID
            paragraph_id: Paragraph ID

        Returns:
            ParagraphMastery or None if not found
        """
        result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.paragraph_id == paragraph_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_student(
        self,
        student_id: int,
        school_id: int
    ) -> List[ParagraphMastery]:
        """
        Get all paragraph mastery records for a student.

        Args:
            student_id: Student ID
            school_id: School ID (tenant isolation)

        Returns:
            List of ParagraphMastery records
        """
        result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.school_id == school_id
            ).order_by(ParagraphMastery.paragraph_id)
        )
        return result.scalars().all()

    async def create(self, mastery: ParagraphMastery) -> ParagraphMastery:
        """
        Create a new paragraph mastery record.

        Args:
            mastery: ParagraphMastery instance

        Returns:
            Created paragraph mastery
        """
        self.db.add(mastery)
        await self.db.commit()
        await self.db.refresh(mastery)
        return mastery

    async def update(self, mastery: ParagraphMastery) -> ParagraphMastery:
        """
        Update an existing paragraph mastery record.

        Args:
            mastery: ParagraphMastery instance with updated fields

        Returns:
            Updated paragraph mastery
        """
        mastery.last_updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(mastery)
        return mastery

    async def upsert(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
        **update_fields
    ) -> ParagraphMastery:
        """
        Create or update paragraph mastery record.

        If a record exists for the student+paragraph, update it.
        Otherwise, create a new record.

        Args:
            student_id: Student ID
            paragraph_id: Paragraph ID
            school_id: School ID
            **update_fields: Fields to set/update (test_score, average_score, etc.)

        Returns:
            Created or updated ParagraphMastery
        """
        existing = await self.get_by_student_paragraph(student_id, paragraph_id)

        if existing:
            # Update existing record
            for key, value in update_fields.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self.update(existing)
        else:
            # Create new record
            new_mastery = ParagraphMastery(
                student_id=student_id,
                paragraph_id=paragraph_id,
                school_id=school_id,
                **update_fields
            )
            return await self.create(new_mastery)

    async def get_chapter_stats(
        self,
        student_id: int,
        chapter_id: int
    ) -> Dict[str, int]:
        """
        Get aggregated paragraph mastery stats for a chapter.

        Used by MasteryService to update ChapterMastery counters.

        Args:
            student_id: Student ID
            chapter_id: Chapter ID

        Returns:
            Dictionary with keys:
            - 'total': Total paragraphs in chapter
            - 'completed': Paragraphs marked as completed
            - 'mastered': Paragraphs with status='mastered'
            - 'struggling': Paragraphs with status='struggling'
        """
        # Query with aggregation
        result = await self.db.execute(
            select(
                func.count(Paragraph.id).label('total'),
                func.count(
                    case((ParagraphMastery.is_completed == True, 1))
                ).label('completed'),
                func.count(
                    case((ParagraphMastery.status == 'mastered', 1))
                ).label('mastered'),
                func.count(
                    case((ParagraphMastery.status == 'struggling', 1))
                ).label('struggling')
            )
            .select_from(Paragraph)
            .outerjoin(
                ParagraphMastery,
                (ParagraphMastery.paragraph_id == Paragraph.id) &
                (ParagraphMastery.student_id == student_id)
            )
            .where(Paragraph.chapter_id == chapter_id)
        )

        row = result.one()

        return {
            'total': row.total or 0,
            'completed': row.completed or 0,
            'mastered': row.mastered or 0,
            'struggling': row.struggling or 0
        }
