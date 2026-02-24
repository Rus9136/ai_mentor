"""
Repository for Exercise data access.
"""
from typing import Optional, List
from sqlalchemy import select, func, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.exercise import Exercise


class ExerciseRepository:
    """Repository for Exercise CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, exercise_id: int) -> Optional[Exercise]:
        """Get exercise by ID (active only)."""
        result = await self.db.execute(
            select(Exercise).where(
                Exercise.id == exercise_id,
                Exercise.is_deleted == False  # noqa: E712
            )
        )
        return result.scalar_one_or_none()

    async def list_by_paragraph(
        self,
        paragraph_id: int,
        difficulty: Optional[str] = None,
        school_id: Optional[int] = None,
    ) -> List[Exercise]:
        """Get exercises for a paragraph, ordered by sort_order.

        Args:
            paragraph_id: Paragraph ID
            difficulty: Filter by difficulty (A, B, C)
            school_id: Filter by school (None = global content)
        """
        query = select(Exercise).where(
            Exercise.paragraph_id == paragraph_id,
            Exercise.is_deleted == False  # noqa: E712
        )

        if difficulty:
            query = query.where(Exercise.difficulty == difficulty.upper())

        if school_id is not None:
            # Global content (school_id IS NULL) + school content
            query = query.where(
                (Exercise.school_id == school_id) | (Exercise.school_id.is_(None))
            )
        else:
            query = query.where(Exercise.school_id.is_(None))

        query = query.order_by(Exercise.sort_order)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def count_by_paragraph(
        self,
        paragraph_id: int,
        difficulty: Optional[str] = None,
    ) -> int:
        """Count exercises for a paragraph."""
        query = select(func.count(Exercise.id)).where(
            Exercise.paragraph_id == paragraph_id,
            Exercise.is_deleted == False  # noqa: E712
        )
        if difficulty:
            query = query.where(Exercise.difficulty == difficulty.upper())
        result = await self.db.execute(query)
        return result.scalar_one()

    async def count_by_difficulty(
        self,
        paragraph_id: int,
    ) -> dict[str, int]:
        """Count exercises by difficulty for a paragraph."""
        query = (
            select(Exercise.difficulty, func.count(Exercise.id))
            .where(
                Exercise.paragraph_id == paragraph_id,
                Exercise.is_deleted == False  # noqa: E712
            )
            .group_by(Exercise.difficulty)
        )
        result = await self.db.execute(query)
        counts = {"A": 0, "B": 0, "C": 0}
        for difficulty, count in result.all():
            if difficulty in counts:
                counts[difficulty] = count
        return counts

    async def create_batch(self, exercises: list[dict]) -> List[Exercise]:
        """Create multiple exercises at once (for import)."""
        objects = [Exercise(**data) for data in exercises]
        self.db.add_all(objects)
        await self.db.flush()
        return objects

    async def delete_by_paragraph(self, paragraph_id: int) -> int:
        """Soft-delete all exercises for a paragraph (for re-import)."""
        result = await self.db.execute(
            select(Exercise).where(
                Exercise.paragraph_id == paragraph_id,
                Exercise.is_deleted == False  # noqa: E712
            )
        )
        exercises = result.scalars().all()
        count = 0
        for ex in exercises:
            ex.is_deleted = True
            count += 1
        await self.db.flush()
        return count
