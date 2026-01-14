"""
Student Content Service.

This service handles fetching content for students with progress calculation.
Uses batch queries to avoid N+1 problems.

The service is read-only for textbooks/chapters/paragraphs lists
(commit only needed for paragraph detail which updates last_accessed_at).
"""

import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload

from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.mastery import ParagraphMastery, ChapterMastery
from app.models.test import Test, TestPurpose
from app.core.config import settings

logger = logging.getLogger(__name__)


class StudentContentService:
    """
    Service for student content access with progress calculation.

    Responsibilities:
    - Get textbooks with progress (batch queries)
    - Get chapters with progress and status
    - Get paragraphs with status and practice info

    Performance:
    - Uses batch queries instead of N+1
    - Single query per aggregation type

    Note: This service mostly reads data. The only write operation
    is updating last_accessed_at in get_paragraph_detail (endpoint commits).
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # =========================================================================
    # Textbooks with Progress
    # =========================================================================

    async def get_textbooks_with_progress(
        self,
        student_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        subject_id: Optional[int] = None,
        grade_level: Optional[int] = None,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get available textbooks with student's progress.

        Uses batch queries to avoid N+1 problem.

        Args:
            student_id: Student ID
            school_id: School ID for access control
            page: Page number (1-based)
            page_size: Number of items per page
            subject_id: Optional filter by subject
            grade_level: Optional filter by grade level (1-11)

        Returns:
            Tuple of (list of dicts with textbook and progress data, total count)
        """
        # Base query for textbooks
        conditions = [
            Textbook.is_deleted == False,
            Textbook.is_active == True,
            or_(
                Textbook.school_id.is_(None),
                Textbook.school_id == school_id
            )
        ]

        # Apply filters
        if subject_id is not None:
            conditions.append(Textbook.subject_id == subject_id)
        if grade_level is not None:
            conditions.append(Textbook.grade_level == grade_level)

        base_query = select(Textbook).where(and_(*conditions))

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # 1. Get available textbooks (global + school-specific) with pagination
        offset = (page - 1) * page_size
        textbooks_result = await self.db.execute(
            base_query
            .options(selectinload(Textbook.subject_rel))
            .order_by(Textbook.grade_level, Textbook.title)
            .offset(offset)
            .limit(page_size)
        )
        textbooks = textbooks_result.scalars().all()

        if not textbooks:
            return [], total

        textbook_ids = [t.id for t in textbooks]

        # 2. Batch: chapters count per textbook
        chapters_count = await self._get_chapters_count_batch(textbook_ids)

        # 3. Batch: paragraphs total per textbook
        paragraphs_total = await self._get_paragraphs_total_batch(textbook_ids)

        # 4. Batch: completed paragraphs per textbook
        paragraphs_completed = await self._get_paragraphs_completed_batch(
            student_id, textbook_ids
        )

        # 5. Batch: completed chapters per textbook
        chapters_completed = await self._get_chapters_completed_batch(
            student_id, textbook_ids
        )

        # 6. Batch: average mastery score per textbook
        mastery_scores = await self._get_mastery_scores_batch(
            student_id, textbook_ids
        )

        # 7. Batch: last activity per textbook
        last_activities = await self._get_last_activity_batch(
            student_id, textbook_ids
        )

        # 8. Build response
        result = []
        for textbook in textbooks:
            tid = textbook.id
            para_total = paragraphs_total.get(tid, 0)
            para_completed = paragraphs_completed.get(tid, 0)
            percentage = int((para_completed / para_total * 100)) if para_total > 0 else 0

            # Calculate mastery level from average score
            avg_score = mastery_scores.get(tid)
            mastery_level = self._calculate_mastery_level(avg_score)

            result.append({
                "textbook": textbook,
                "progress": {
                    "chapters_total": chapters_count.get(tid, 0),
                    "chapters_completed": chapters_completed.get(tid, 0),
                    "paragraphs_total": para_total,
                    "paragraphs_completed": para_completed,
                    "percentage": percentage,
                },
                "mastery_level": mastery_level,
                "last_activity": last_activities.get(tid),
            })

        logger.info(
            f"Student {student_id} retrieved {len(result)} textbooks with progress"
        )
        return result, total

    async def _get_chapters_count_batch(
        self,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count chapters per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(Chapter.id).label('count')
            )
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_paragraphs_total_batch(
        self,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count paragraphs per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(Paragraph.id).label('count')
            )
            .join(Paragraph, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False,
                Paragraph.is_deleted == False
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_paragraphs_completed_batch(
        self,
        student_id: int,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count completed paragraphs per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(ParagraphMastery.id).label('count')
            )
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False,
                Paragraph.is_deleted == False,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_chapters_completed_batch(
        self,
        student_id: int,
        textbook_ids: List[int]
    ) -> Dict[int, int]:
        """
        Batch query: count completed chapters per textbook.

        A chapter is completed when all its paragraphs are completed.
        Uses subquery to compare total vs completed paragraphs per chapter.
        """
        # Subquery: total paragraphs per chapter
        total_subq = (
            select(
                Paragraph.chapter_id,
                func.count(Paragraph.id).label('total')
            )
            .where(Paragraph.is_deleted == False)
            .group_by(Paragraph.chapter_id)
            .subquery()
        )

        # Subquery: completed paragraphs per chapter for this student
        completed_subq = (
            select(
                Paragraph.chapter_id,
                func.count(ParagraphMastery.id).label('completed')
            )
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .where(
                Paragraph.is_deleted == False,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
            .group_by(Paragraph.chapter_id)
            .subquery()
        )

        # Main query: count chapters where completed >= total
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.count(Chapter.id).label('count')
            )
            .outerjoin(total_subq, Chapter.id == total_subq.c.chapter_id)
            .outerjoin(completed_subq, Chapter.id == completed_subq.c.chapter_id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False,
                total_subq.c.total > 0,  # Has at least one paragraph
                func.coalesce(completed_subq.c.completed, 0) >= total_subq.c.total
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.count for row in result.fetchall()}

    async def _get_mastery_scores_batch(
        self,
        student_id: int,
        textbook_ids: List[int]
    ) -> Dict[int, Optional[float]]:
        """Batch query: average mastery score per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.avg(ChapterMastery.mastery_score).label('avg_score')
            )
            .join(Chapter, ChapterMastery.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                Chapter.is_deleted == False,
                ChapterMastery.student_id == student_id
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.avg_score for row in result.fetchall()}

    async def _get_last_activity_batch(
        self,
        student_id: int,
        textbook_ids: List[int]
    ) -> Dict[int, Optional[datetime]]:
        """Batch query: last activity timestamp per textbook."""
        result = await self.db.execute(
            select(
                Chapter.textbook_id,
                func.max(ParagraphMastery.last_updated_at).label('last_activity')
            )
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id.in_(textbook_ids),
                ParagraphMastery.student_id == student_id
            )
            .group_by(Chapter.textbook_id)
        )
        return {row.textbook_id: row.last_activity for row in result.fetchall()}

    # =========================================================================
    # Chapters with Progress
    # =========================================================================

    async def get_chapters_with_progress(
        self,
        textbook_id: int,
        student_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get chapters for a textbook with student's progress.

        Args:
            textbook_id: Textbook ID
            student_id: Student ID
            school_id: School ID for access control
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (list of dicts with chapter and progress data, total count)
        """
        # Base query for chapters
        base_query = select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.is_deleted == False
        )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get chapters ordered by order field with pagination
        offset = (page - 1) * page_size
        chapters_result = await self.db.execute(
            base_query.order_by(Chapter.order).offset(offset).limit(page_size)
        )
        chapters = chapters_result.scalars().all()

        if not chapters:
            return [], total

        chapter_ids = [c.id for c in chapters]

        # Batch: paragraphs total per chapter
        para_total = await self._get_paragraphs_per_chapter_batch(chapter_ids)

        # Batch: completed paragraphs per chapter
        para_completed = await self._get_completed_per_chapter_batch(
            student_id, chapter_ids
        )

        # Batch: chapter mastery
        chapter_mastery = await self._get_chapter_mastery_batch(
            student_id, chapter_ids
        )

        # Batch: summative test availability
        has_summative = await self._get_summative_test_batch(chapter_ids)

        # Build response with status calculation
        result = []
        prev_completed = True  # First chapter is always unlocked

        for chapter in chapters:
            cid = chapter.id
            ch_para_total = para_total.get(cid, 0)
            ch_para_completed = para_completed.get(cid, 0)
            percentage = int((ch_para_completed / ch_para_total * 100)) if ch_para_total > 0 else 0

            mastery = chapter_mastery.get(cid, {})
            mastery_level = mastery.get("level")
            mastery_score = mastery.get("score")
            summative_passed = mastery.get("summative_passed")

            # Determine status
            if ch_para_completed >= ch_para_total and ch_para_total > 0:
                ch_status = "completed"
            elif ch_para_completed > 0:
                ch_status = "in_progress"
            elif prev_completed:
                ch_status = "not_started"
            else:
                ch_status = "locked"

            # Update for next iteration
            prev_completed = (ch_status == "completed")

            result.append({
                "chapter": chapter,
                "progress": {
                    "paragraphs_total": ch_para_total,
                    "paragraphs_completed": ch_para_completed,
                    "percentage": percentage,
                },
                "status": ch_status,
                "mastery_level": mastery_level,
                "mastery_score": mastery_score,
                "has_summative_test": has_summative.get(cid, False),
                "summative_passed": summative_passed,
            })

        logger.info(
            f"Student {student_id} retrieved {len(result)} chapters "
            f"for textbook {textbook_id}"
        )
        return result, total

    async def _get_paragraphs_per_chapter_batch(
        self,
        chapter_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count paragraphs per chapter."""
        result = await self.db.execute(
            select(
                Paragraph.chapter_id,
                func.count(Paragraph.id).label('count')
            )
            .where(
                Paragraph.chapter_id.in_(chapter_ids),
                Paragraph.is_deleted == False
            )
            .group_by(Paragraph.chapter_id)
        )
        return {row.chapter_id: row.count for row in result.fetchall()}

    async def _get_completed_per_chapter_batch(
        self,
        student_id: int,
        chapter_ids: List[int]
    ) -> Dict[int, int]:
        """Batch query: count completed paragraphs per chapter."""
        result = await self.db.execute(
            select(
                Paragraph.chapter_id,
                func.count(ParagraphMastery.id).label('count')
            )
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .where(
                Paragraph.chapter_id.in_(chapter_ids),
                Paragraph.is_deleted == False,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
            .group_by(Paragraph.chapter_id)
        )
        return {row.chapter_id: row.count for row in result.fetchall()}

    async def _get_chapter_mastery_batch(
        self,
        student_id: int,
        chapter_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """Batch query: mastery data per chapter."""
        result = await self.db.execute(
            select(ChapterMastery).where(
                ChapterMastery.chapter_id.in_(chapter_ids),
                ChapterMastery.student_id == student_id
            )
        )
        mastery_records = result.scalars().all()

        return {
            m.chapter_id: {
                "level": m.mastery_level,
                "score": m.mastery_score,
                "summative_passed": m.summative_passed,
            }
            for m in mastery_records
        }

    async def _get_summative_test_batch(
        self,
        chapter_ids: List[int]
    ) -> Dict[int, bool]:
        """Batch query: check summative test availability per chapter."""
        result = await self.db.execute(
            select(Test.chapter_id)
            .where(
                Test.chapter_id.in_(chapter_ids),
                Test.test_purpose == TestPurpose.SUMMATIVE,
                Test.is_active == True,
                Test.is_deleted == False
            )
            .distinct()
        )
        chapters_with_test = {row[0] for row in result.fetchall()}
        return {cid: cid in chapters_with_test for cid in chapter_ids}

    # =========================================================================
    # Paragraphs with Progress
    # =========================================================================

    async def get_paragraphs_with_progress(
        self,
        chapter_id: int,
        student_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 50,
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Get paragraphs for a chapter with student's progress.

        Args:
            chapter_id: Chapter ID
            student_id: Student ID
            school_id: School ID for access control
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (list of dicts with paragraph and progress data, total count)
        """
        # Base query for paragraphs
        base_query = select(Paragraph).where(
            Paragraph.chapter_id == chapter_id,
            Paragraph.is_deleted == False
        )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paragraphs ordered with pagination
        offset = (page - 1) * page_size
        paragraphs_result = await self.db.execute(
            base_query.order_by(Paragraph.order).offset(offset).limit(page_size)
        )
        paragraphs = paragraphs_result.scalars().all()

        if not paragraphs:
            return [], total

        paragraph_ids = [p.id for p in paragraphs]

        # Batch: mastery data per paragraph
        paragraph_mastery = await self._get_paragraph_mastery_batch(
            student_id, paragraph_ids
        )

        # Batch: practice test availability
        has_practice = await self._get_practice_test_batch(paragraph_ids)

        # Build response
        result = []
        for para in paragraphs:
            pid = para.id
            mastery = paragraph_mastery.get(pid, {})

            # Determine status
            if mastery.get("is_completed"):
                para_status = "completed"
            elif mastery:
                para_status = "in_progress"
            else:
                para_status = "not_started"

            # Estimate reading time
            word_count = len(para.content.split()) if para.content else 0
            estimated_time = max(3, min(15, word_count // 200 + 3))

            result.append({
                "paragraph": para,
                "status": para_status,
                "practice_score": mastery.get("best_score"),
                "estimated_time": estimated_time,
                "has_practice": has_practice.get(pid, False),
            })

        logger.info(
            f"Student {student_id} retrieved {len(result)} paragraphs "
            f"for chapter {chapter_id}"
        )
        return result, total

    async def _get_paragraph_mastery_batch(
        self,
        student_id: int,
        paragraph_ids: List[int]
    ) -> Dict[int, Dict[str, Any]]:
        """Batch query: mastery data per paragraph."""
        result = await self.db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.paragraph_id.in_(paragraph_ids),
                ParagraphMastery.student_id == student_id
            )
        )
        mastery_records = result.scalars().all()

        return {
            m.paragraph_id: {
                "is_completed": m.is_completed,
                "best_score": m.best_score,
            }
            for m in mastery_records
        }

    async def _get_practice_test_batch(
        self,
        paragraph_ids: List[int]
    ) -> Dict[int, bool]:
        """Batch query: check practice test availability per paragraph."""
        result = await self.db.execute(
            select(Test.paragraph_id)
            .where(
                Test.paragraph_id.in_(paragraph_ids),
                Test.test_purpose == TestPurpose.PRACTICE,
                Test.is_active == True,
                Test.is_deleted == False
            )
            .distinct()
        )
        paragraphs_with_test = {row[0] for row in result.fetchall()}
        return {pid: pid in paragraphs_with_test for pid in paragraph_ids}

    # =========================================================================
    # Utility Methods
    # =========================================================================

    def _calculate_mastery_level(
        self,
        avg_score: Optional[float]
    ) -> Optional[str]:
        """
        Calculate mastery level from average score.

        Uses thresholds from settings:
        - Score >= MASTERY_LEVEL_A_THRESHOLD (85) -> "A"
        - Score >= MASTERY_LEVEL_B_THRESHOLD (60) -> "B"
        - Score < 60 -> "C"
        """
        if avg_score is None:
            return None

        if avg_score >= settings.MASTERY_LEVEL_A_THRESHOLD:
            return "A"
        elif avg_score >= settings.MASTERY_LEVEL_B_THRESHOLD:
            return "B"
        else:
            return "C"
