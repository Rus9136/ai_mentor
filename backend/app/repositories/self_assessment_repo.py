"""
Repository for ParagraphSelfAssessment data access.

Append-only: only create and read operations.
"""
import logging
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Tuple

from sqlalchemy import select, func, case, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.learning import ParagraphSelfAssessment
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter

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

    # ========================================================================
    # TEACHER ANALYTICS
    # ========================================================================

    async def get_summary_by_paragraph(
        self,
        student_ids: List[int],
    ) -> List[dict]:
        """
        Get aggregated self-assessment counts per paragraph for given students.

        Returns list of dicts with paragraph_id, paragraph_title, chapter_id,
        chapter_title, total, understood, questions, difficult counts.
        """
        if not student_ids:
            return []

        query = (
            select(
                ParagraphSelfAssessment.paragraph_id,
                Paragraph.title.label("paragraph_title"),
                Chapter.id.label("chapter_id"),
                Chapter.title.label("chapter_title"),
                func.count().label("total"),
                func.sum(case(
                    (ParagraphSelfAssessment.rating == "understood", 1),
                    else_=0
                )).label("understood"),
                func.sum(case(
                    (ParagraphSelfAssessment.rating == "questions", 1),
                    else_=0
                )).label("questions"),
                func.sum(case(
                    (ParagraphSelfAssessment.rating == "difficult", 1),
                    else_=0
                )).label("difficult"),
            )
            .join(Paragraph, Paragraph.id == ParagraphSelfAssessment.paragraph_id)
            .join(Chapter, Chapter.id == Paragraph.chapter_id)
            .where(ParagraphSelfAssessment.student_id.in_(student_ids))
            .group_by(
                ParagraphSelfAssessment.paragraph_id,
                Paragraph.title,
                Chapter.id,
                Chapter.title,
            )
            .order_by(func.sum(case(
                (ParagraphSelfAssessment.rating == "difficult", 1),
                else_=0
            )).desc())
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {
                "paragraph_id": row.paragraph_id,
                "paragraph_title": row.paragraph_title,
                "chapter_id": row.chapter_id,
                "chapter_title": row.chapter_title,
                "total": row.total,
                "understood": row.understood,
                "questions": row.questions,
                "difficult": row.difficult,
            }
            for row in rows
        ]

    async def get_metacognitive_alerts(
        self,
        student_ids: List[int],
        limit: int = 50,
    ) -> Tuple[List[ParagraphSelfAssessment], List[ParagraphSelfAssessment]]:
        """
        Find students with metacognitive mismatches.

        Returns:
            Tuple of (overconfident_list, underconfident_list)
            - overconfident: rated "understood" but practice_score < 60
            - underconfident: rated "difficult" but practice_score > 80
        """
        if not student_ids:
            return [], []

        base = (
            select(ParagraphSelfAssessment)
            .where(
                ParagraphSelfAssessment.student_id.in_(student_ids),
                ParagraphSelfAssessment.practice_score.isnot(None),
            )
            .order_by(ParagraphSelfAssessment.created_at.desc())
            .limit(limit)
        )

        over_q = base.where(
            ParagraphSelfAssessment.rating == "understood",
            ParagraphSelfAssessment.practice_score < 60,
        )
        under_q = base.where(
            ParagraphSelfAssessment.rating == "difficult",
            ParagraphSelfAssessment.practice_score > 80,
        )

        over_result = await self.db.execute(over_q)
        under_result = await self.db.execute(under_q)

        return (
            list(over_result.scalars().all()),
            list(under_result.scalars().all()),
        )

    async def get_student_assessments(
        self,
        student_id: int,
        limit: int = 100,
    ) -> List[ParagraphSelfAssessment]:
        """
        Get all self-assessments for a student, newest first.
        Used for teacher view of individual student.
        """
        result = await self.db.execute(
            select(ParagraphSelfAssessment)
            .where(ParagraphSelfAssessment.student_id == student_id)
            .order_by(ParagraphSelfAssessment.created_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
