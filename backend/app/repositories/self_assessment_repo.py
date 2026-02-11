"""
Repository for ParagraphSelfAssessment data access.

Append-only: only create and read operations.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import ParagraphSelfAssessment

logger = logging.getLogger(__name__)


class SelfAssessmentRepository:
    """Repository for append-only self-assessment records."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        student_id: int,
        paragraph_id: int,
        school_id: int,
        rating: str,
        mastery_impact: float,
        practice_score: Optional[float] = None,
        time_spent: Optional[int] = None,
    ) -> ParagraphSelfAssessment:
        """
        Create a new self-assessment record.

        Returns:
            Created ParagraphSelfAssessment record
        """
        record = ParagraphSelfAssessment(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            rating=rating,
            mastery_impact=mastery_impact,
            practice_score=practice_score,
            time_spent=time_spent,
        )
        self.db.add(record)
        await self.db.commit()
        await self.db.refresh(record)
        return record

    async def find_recent_duplicate(
        self,
        student_id: int,
        paragraph_id: int,
        rating: str,
        window_seconds: int = 60,
    ) -> Optional[ParagraphSelfAssessment]:
        """
        Find a duplicate assessment within the last N seconds.

        Used for idempotency in offline sync scenarios.
        If the same (student_id, paragraph_id, rating) was submitted
        within the window, return the existing record instead of creating a new one.
        """
        cutoff = datetime.now(timezone.utc) - timedelta(seconds=window_seconds)
        result = await self.db.execute(
            select(ParagraphSelfAssessment)
            .where(
                ParagraphSelfAssessment.student_id == student_id,
                ParagraphSelfAssessment.paragraph_id == paragraph_id,
                ParagraphSelfAssessment.rating == rating,
                ParagraphSelfAssessment.created_at >= cutoff,
            )
            .order_by(ParagraphSelfAssessment.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def get_history(
        self,
        student_id: int,
        paragraph_id: int,
        limit: int = 10,
    ) -> List[ParagraphSelfAssessment]:
        """
        Get self-assessment history for a student+paragraph, newest first.
        """
        result = await self.db.execute(
            select(ParagraphSelfAssessment)
            .where(
                ParagraphSelfAssessment.student_id == student_id,
                ParagraphSelfAssessment.paragraph_id == paragraph_id,
            )
            .order_by(ParagraphSelfAssessment.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
