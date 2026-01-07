"""
Mastery Analytics Service.

Handles mastery calculations, distributions, and analytics.
"""

import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.models.class_student import ClassStudent
from app.models.mastery import ChapterMastery, ParagraphMastery
from app.models.paragraph import Paragraph
from app.schemas.teacher_dashboard import (
    ClassTrend,
    MasteryDistribution,
    MasteryTrendsResponse,
    StrugglingTopicResponse,
)

logger = logging.getLogger(__name__)


class MasteryAnalyticsService:
    """Service for mastery calculations and analytics."""

    def __init__(self, db: AsyncSession):
        self.db = db

    def calculate_mastery_distribution(
        self,
        students_mastery: List[Dict[str, Any]]
    ) -> MasteryDistribution:
        """
        Calculate A/B/C distribution from student mastery data.

        Args:
            students_mastery: List of dicts with 'mastery_level' key

        Returns:
            MasteryDistribution with counts per level
        """
        distribution = MasteryDistribution()

        for sm in students_mastery:
            level = sm.get("mastery_level")
            if level == "A":
                distribution.level_a += 1
            elif level == "B":
                distribution.level_b += 1
            elif level == "C":
                distribution.level_c += 1
            else:
                distribution.not_started += 1

        return distribution

    async def get_mastery_distribution_for_students(
        self,
        student_ids: List[int]
    ) -> MasteryDistribution:
        """
        Get mastery distribution for a set of students.

        Args:
            student_ids: List of student IDs

        Returns:
            MasteryDistribution
        """
        if not student_ids:
            return MasteryDistribution()

        mastery_result = await self.db.execute(
            select(ChapterMastery.mastery_level, func.count())
            .where(ChapterMastery.student_id.in_(student_ids))
            .group_by(ChapterMastery.mastery_level)
        )

        distribution = MasteryDistribution()
        students_with_mastery = 0

        for row in mastery_result.fetchall():
            level, count = row
            if level == "A":
                distribution.level_a = count
            elif level == "B":
                distribution.level_b = count
            elif level == "C":
                distribution.level_c = count
            students_with_mastery += count

        distribution.not_started = max(0, len(student_ids) - students_with_mastery)
        return distribution

    async def get_average_score_for_students(
        self,
        student_ids: List[int]
    ) -> float:
        """
        Get average mastery score for students.

        Args:
            student_ids: List of student IDs

        Returns:
            Average score (0.0 if no data)
        """
        if not student_ids:
            return 0.0

        avg_result = await self.db.execute(
            select(func.avg(ChapterMastery.mastery_score))
            .where(ChapterMastery.student_id.in_(student_ids))
        )
        return avg_result.scalar() or 0.0

    async def get_average_progress_for_students(
        self,
        student_ids: List[int]
    ) -> int:
        """
        Get average progress percentage for students.

        Args:
            student_ids: List of student IDs

        Returns:
            Average progress percentage (0 if no data)
        """
        if not student_ids:
            return 0

        progress_result = await self.db.execute(
            select(func.avg(ChapterMastery.progress_percentage))
            .where(ChapterMastery.student_id.in_(student_ids))
        )
        return int(progress_result.scalar() or 0)

    async def get_struggling_topics(
        self,
        student_ids: List[int],
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[StrugglingTopicResponse], int]:
        """
        Get topics where students are struggling.

        Args:
            student_ids: List of student IDs to analyze
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Tuple of (list of StrugglingTopicResponse, total count)
        """
        if not student_ids:
            return [], 0

        # Base subquery for struggling topics
        struggling_count_expr = func.count(ParagraphMastery.id).filter(
            ParagraphMastery.status == "struggling"
        )

        base_query = (
            select(
                Paragraph.id,
                Paragraph.title,
                Chapter.id,
                Chapter.title,
                struggling_count_expr.label("struggling_count"),
                func.count(ParagraphMastery.id).label("total_count"),
                func.avg(ParagraphMastery.average_score).label("avg_score")
            )
            .join(ParagraphMastery, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Chapter.id == Paragraph.chapter_id)
            .where(ParagraphMastery.student_id.in_(student_ids))
            .group_by(Paragraph.id, Paragraph.title, Chapter.id, Chapter.title)
            .having(struggling_count_expr > 0)
        )

        # Get total count
        count_subquery = base_query.subquery()
        count_query = select(func.count()).select_from(count_subquery)
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results
        offset = (page - 1) * page_size
        result = await self.db.execute(
            base_query
            .order_by(desc(struggling_count_expr))
            .offset(offset)
            .limit(page_size)
        )

        topics = []
        for row in result.fetchall():
            para_id, para_title, ch_id, ch_title, struggling, total_students, avg_score = row
            topics.append(StrugglingTopicResponse(
                paragraph_id=para_id,
                paragraph_title=para_title,
                chapter_id=ch_id,
                chapter_title=ch_title,
                struggling_count=struggling,
                total_students=total_students,
                struggling_percentage=round(100 * struggling / total_students, 1) if total_students > 0 else 0.0,
                average_score=round((avg_score or 0) * 100, 1)
            ))

        return topics, total

    async def get_mastery_trends(
        self,
        classes_data: List[Dict[str, Any]],
        period: str = "weekly"
    ) -> MasteryTrendsResponse:
        """
        Get mastery trends across classes.

        Args:
            classes_data: List of class data with id, name, average_score
            period: "weekly" or "monthly"

        Returns:
            MasteryTrendsResponse
        """
        end_date = datetime.utcnow().date()
        if period == "weekly":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        class_trends = []
        total_change = 0.0

        for cls in classes_data:
            # Simplified: return current average as both previous and current
            # TODO: Implement actual historical comparison
            class_trends.append(ClassTrend(
                class_id=cls["id"],
                class_name=cls["name"],
                previous_average=cls["average_score"],
                current_average=cls["average_score"],
                change_percentage=0.0,
                trend="stable",
                promoted_to_a=0,
                demoted_to_c=0
            ))

        overall_trend = "stable"
        if total_change > 5:
            overall_trend = "improving"
        elif total_change < -5:
            overall_trend = "declining"

        return MasteryTrendsResponse(
            period=period,
            start_date=start_date,
            end_date=end_date,
            overall_trend=overall_trend,
            overall_change_percentage=total_change,
            class_trends=class_trends
        )

    async def get_dashboard_distribution(
        self,
        class_ids: List[int]
    ) -> tuple[int, MasteryDistribution, float]:
        """
        Get dashboard mastery distribution across all classes.

        Args:
            class_ids: List of class IDs

        Returns:
            Tuple of (total_students, distribution, average_score)
        """
        if not class_ids:
            return 0, MasteryDistribution(), 0.0

        # Get total students count
        students_result = await self.db.execute(
            select(func.count(func.distinct(ClassStudent.student_id)))
            .where(ClassStudent.class_id.in_(class_ids))
        )
        total_students = students_result.scalar() or 0

        # Get mastery distribution
        mastery_result = await self.db.execute(
            select(
                ChapterMastery.mastery_level,
                func.count(func.distinct(ChapterMastery.student_id))
            )
            .join(ClassStudent, ClassStudent.student_id == ChapterMastery.student_id)
            .where(ClassStudent.class_id.in_(class_ids))
            .group_by(ChapterMastery.mastery_level)
        )

        distribution = MasteryDistribution()
        students_with_mastery = 0

        for row in mastery_result.fetchall():
            level, count = row
            if level == "A":
                distribution.level_a = count
            elif level == "B":
                distribution.level_b = count
            elif level == "C":
                distribution.level_c = count
            students_with_mastery += count

        distribution.not_started = max(0, total_students - students_with_mastery)

        # Get average score
        avg_result = await self.db.execute(
            select(func.avg(ChapterMastery.mastery_score))
            .join(ClassStudent, ClassStudent.student_id == ChapterMastery.student_id)
            .where(ClassStudent.class_id.in_(class_ids))
        )
        avg_score = avg_result.scalar() or 0.0

        return total_students, distribution, avg_score
