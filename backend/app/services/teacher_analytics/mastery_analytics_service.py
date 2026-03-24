"""
Mastery Analytics Service.

Handles mastery calculations, distributions, and analytics.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.chapter import Chapter
from app.models.class_student import ClassStudent
from app.models.mastery import ChapterMastery, MasteryHistory, ParagraphMastery
from app.models.paragraph import Paragraph
from app.models.textbook import Textbook
from app.schemas.teacher_dashboard import (
    AnalyticsSummaryResponse,
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
        """Get topics where students are struggling."""
        if not student_ids:
            return [], 0

        struggling_count_expr = func.count(ParagraphMastery.id).filter(
            ParagraphMastery.status == "struggling"
        )

        base_query = (
            select(
                Paragraph.id,
                Paragraph.title,
                Chapter.id,
                Chapter.title,
                Textbook.title.label("textbook_title"),
                struggling_count_expr.label("struggling_count"),
                func.count(ParagraphMastery.id).label("total_count"),
                func.avg(ParagraphMastery.average_score).label("avg_score")
            )
            .join(ParagraphMastery, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Chapter.id == Paragraph.chapter_id)
            .join(Textbook, Textbook.id == Chapter.textbook_id)
            .where(ParagraphMastery.student_id.in_(student_ids))
            .group_by(Paragraph.id, Paragraph.title, Chapter.id, Chapter.title, Textbook.title)
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
            para_id, para_title, ch_id, ch_title, tb_title, struggling, total_students, avg_score = row
            topics.append(StrugglingTopicResponse(
                paragraph_id=para_id,
                paragraph_title=para_title,
                chapter_id=ch_id,
                chapter_title=ch_title,
                textbook_title=tb_title,
                struggling_count=struggling,
                total_students=total_students,
                struggling_percentage=round(100 * struggling / total_students, 1) if total_students > 0 else 0.0,
                average_score=round((avg_score or 0) * 100, 1)
            ))

        return topics, total

    async def get_mastery_trends(
        self,
        classes_data: List[Dict[str, Any]],
        student_ids_by_class: Dict[int, List[int]],
        period: str = "weekly"
    ) -> MasteryTrendsResponse:
        """
        Get mastery trends using MasteryHistory records.

        Compares average mastery scores between start and end of period
        by querying actual historical records.
        """
        end_date = datetime.now(timezone.utc)
        if period == "weekly":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        class_trends = []
        total_current = 0.0
        total_previous = 0.0
        classes_with_data = 0

        for cls in classes_data:
            class_id = cls["id"]
            s_ids = student_ids_by_class.get(class_id, [])
            if not s_ids:
                class_trends.append(ClassTrend(
                    class_id=class_id,
                    class_name=cls["name"],
                    previous_average=cls["average_score"],
                    current_average=cls["average_score"],
                    change_percentage=0.0,
                    trend="stable",
                    promoted_to_a=0,
                    demoted_to_c=0,
                ))
                continue

            # Get average mastery score at start of period (latest record before start_date per student)
            prev_subq = (
                select(
                    MasteryHistory.student_id,
                    func.avg(MasteryHistory.new_score).label("avg_score"),
                )
                .where(
                    MasteryHistory.student_id.in_(s_ids),
                    MasteryHistory.recorded_at < start_date,
                    MasteryHistory.chapter_id.isnot(None),
                )
                .group_by(MasteryHistory.student_id)
            ).subquery()

            prev_result = await self.db.execute(
                select(func.avg(prev_subq.c.avg_score))
            )
            previous_avg = prev_result.scalar()

            # Get average mastery score in current period (records within period)
            curr_subq = (
                select(
                    MasteryHistory.student_id,
                    func.avg(MasteryHistory.new_score).label("avg_score"),
                )
                .where(
                    MasteryHistory.student_id.in_(s_ids),
                    MasteryHistory.recorded_at >= start_date,
                    MasteryHistory.chapter_id.isnot(None),
                )
                .group_by(MasteryHistory.student_id)
            ).subquery()

            curr_result = await self.db.execute(
                select(func.avg(curr_subq.c.avg_score))
            )
            current_avg = curr_result.scalar()

            # If no history data, fall back to current live scores
            if current_avg is None:
                current_avg = cls["average_score"]
            else:
                current_avg = round(current_avg * 100, 1)

            if previous_avg is None:
                previous_avg = current_avg  # No historical data → show as stable
            else:
                previous_avg = round(previous_avg * 100, 1)

            change = round(current_avg - previous_avg, 1)

            # Count level promotions/demotions in the period
            promoted = 0
            demoted = 0
            level_changes = await self.db.execute(
                select(
                    MasteryHistory.previous_level,
                    MasteryHistory.new_level,
                    func.count().label("cnt"),
                )
                .where(
                    MasteryHistory.student_id.in_(s_ids),
                    MasteryHistory.recorded_at >= start_date,
                    MasteryHistory.chapter_id.isnot(None),
                    MasteryHistory.previous_level.isnot(None),
                    MasteryHistory.new_level.isnot(None),
                    MasteryHistory.previous_level != MasteryHistory.new_level,
                )
                .group_by(MasteryHistory.previous_level, MasteryHistory.new_level)
            )
            for row in level_changes.fetchall():
                prev_level, new_level, cnt = row
                if new_level == "A" and prev_level in ("B", "C"):
                    promoted += cnt
                elif new_level == "C" and prev_level in ("A", "B"):
                    demoted += cnt

            trend = "stable"
            if change > 3:
                trend = "improving"
            elif change < -3:
                trend = "declining"

            class_trends.append(ClassTrend(
                class_id=class_id,
                class_name=cls["name"],
                previous_average=previous_avg,
                current_average=current_avg,
                change_percentage=change,
                trend=trend,
                promoted_to_a=promoted,
                demoted_to_c=demoted,
            ))

            total_current += current_avg
            total_previous += previous_avg
            classes_with_data += 1

        overall_change = 0.0
        if classes_with_data > 0:
            overall_change = round(
                (total_current - total_previous) / classes_with_data, 1
            )

        overall_trend = "stable"
        if overall_change > 3:
            overall_trend = "improving"
        elif overall_change < -3:
            overall_trend = "declining"

        return MasteryTrendsResponse(
            period=period,
            start_date=start_date.date(),
            end_date=end_date.date(),
            overall_trend=overall_trend,
            overall_change_percentage=overall_change,
            class_trends=class_trends,
        )

    async def get_analytics_summary(
        self,
        student_ids: List[int],
        class_ids: List[int],
    ) -> AnalyticsSummaryResponse:
        """Get quick summary metrics for dashboard header."""
        if not student_ids:
            return AnalyticsSummaryResponse()

        total_students = len(student_ids)

        # Average mastery score
        avg_result = await self.db.execute(
            select(func.avg(ParagraphMastery.average_score))
            .where(ParagraphMastery.student_id.in_(student_ids))
        )
        avg_mastery = round((avg_result.scalar() or 0) * 100, 1)

        # Count struggling topics
        struggling_count_expr = func.count(ParagraphMastery.id).filter(
            ParagraphMastery.status == "struggling"
        )
        struggling_q = (
            select(func.count())
            .select_from(
                select(Paragraph.id)
                .join(ParagraphMastery, ParagraphMastery.paragraph_id == Paragraph.id)
                .where(ParagraphMastery.student_id.in_(student_ids))
                .group_by(Paragraph.id)
                .having(struggling_count_expr > 0)
                .subquery()
            )
        )
        struggling_topics_count = (await self.db.execute(struggling_q)).scalar() or 0

        # Count metacognitive alerts
        from app.models.learning import ParagraphSelfAssessment
        over_count = await self.db.execute(
            select(func.count())
            .where(
                ParagraphSelfAssessment.student_id.in_(student_ids),
                ParagraphSelfAssessment.practice_score.isnot(None),
                ParagraphSelfAssessment.rating == "understood",
                ParagraphSelfAssessment.practice_score < 60,
            )
        )
        under_count = await self.db.execute(
            select(func.count())
            .where(
                ParagraphSelfAssessment.student_id.in_(student_ids),
                ParagraphSelfAssessment.practice_score.isnot(None),
                ParagraphSelfAssessment.rating == "difficult",
                ParagraphSelfAssessment.practice_score > 80,
            )
        )
        alerts_count = (over_count.scalar() or 0) + (under_count.scalar() or 0)

        # Active students (activity in last 7 days)
        week_ago = datetime.now(timezone.utc) - timedelta(days=7)
        active_result = await self.db.execute(
            select(func.count(func.distinct(ParagraphMastery.student_id)))
            .where(
                ParagraphMastery.student_id.in_(student_ids),
                ParagraphMastery.last_updated_at >= week_ago,
            )
        )
        active_count = active_result.scalar() or 0

        return AnalyticsSummaryResponse(
            total_students=total_students,
            average_mastery=avg_mastery,
            struggling_topics_count=struggling_topics_count,
            metacognitive_alerts_count=alerts_count,
            active_students_count=active_count,
        )

    async def get_dashboard_distribution(
        self,
        class_ids: List[int]
    ) -> tuple[int, MasteryDistribution, float]:
        if not class_ids:
            return 0, MasteryDistribution(), 0.0

        students_result = await self.db.execute(
            select(func.count(func.distinct(ClassStudent.student_id)))
            .where(ClassStudent.class_id.in_(class_ids))
        )
        total_students = students_result.scalar() or 0

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

        avg_result = await self.db.execute(
            select(func.avg(ChapterMastery.mastery_score))
            .join(ClassStudent, ClassStudent.student_id == ChapterMastery.student_id)
            .where(ClassStudent.class_id.in_(class_ids))
        )
        avg_score = avg_result.scalar() or 0.0

        return total_students, distribution, avg_score
