"""
Repository for ChapterMastery data access.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.mastery import ChapterMastery


class ChapterMasteryRepository:
    """Repository for ChapterMastery CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_student_chapter(
        self,
        student_id: int,
        chapter_id: int
    ) -> Optional[ChapterMastery]:
        """
        Get chapter mastery record for a specific student and chapter.

        Args:
            student_id: Student ID
            chapter_id: Chapter ID

        Returns:
            ChapterMastery or None if not found
        """
        result = await self.db.execute(
            select(ChapterMastery).where(
                ChapterMastery.student_id == student_id,
                ChapterMastery.chapter_id == chapter_id
            )
        )
        return result.scalar_one_or_none()

    async def get_by_student(
        self,
        student_id: int,
        school_id: int
    ) -> List[ChapterMastery]:
        """
        Get all chapter mastery records for a student.

        Args:
            student_id: Student ID
            school_id: School ID (tenant isolation)

        Returns:
            List of ChapterMastery records
        """
        result = await self.db.execute(
            select(ChapterMastery).where(
                ChapterMastery.student_id == student_id,
                ChapterMastery.school_id == school_id
            ).order_by(ChapterMastery.chapter_id)
        )
        return result.scalars().all()

    async def create(self, mastery: ChapterMastery) -> ChapterMastery:
        """
        Create a new chapter mastery record.

        Args:
            mastery: ChapterMastery instance

        Returns:
            Created chapter mastery
        """
        self.db.add(mastery)
        await self.db.commit()
        await self.db.refresh(mastery)
        return mastery

    async def update(self, mastery: ChapterMastery) -> ChapterMastery:
        """
        Update an existing chapter mastery record.

        Args:
            mastery: ChapterMastery instance with updated fields

        Returns:
            Updated chapter mastery
        """
        mastery.last_updated_at = datetime.utcnow()
        await self.db.commit()
        await self.db.refresh(mastery)
        return mastery

    async def upsert(
        self,
        student_id: int,
        chapter_id: int,
        school_id: int,
        **update_fields
    ) -> ChapterMastery:
        """
        Create or update chapter mastery record.

        If a record exists for the student+chapter, update it.
        Otherwise, create a new record.

        Args:
            student_id: Student ID
            chapter_id: Chapter ID
            school_id: School ID
            **update_fields: Fields to set/update (mastery_level, mastery_score, etc.)

        Returns:
            Created or updated ChapterMastery
        """
        existing = await self.get_by_student_chapter(student_id, chapter_id)

        if existing:
            # Update existing record
            for key, value in update_fields.items():
                if hasattr(existing, key):
                    setattr(existing, key, value)
            return await self.update(existing)
        else:
            # Create new record
            new_mastery = ChapterMastery(
                student_id=student_id,
                chapter_id=chapter_id,
                school_id=school_id,
                **update_fields
            )
            return await self.create(new_mastery)
