"""
Teacher Analytics Service - Orchestrator.

Coordinates specialized services for Teacher Dashboard.
"""

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.teacher_dashboard import (
    AnalyticsSummaryResponse,
    ClassOverviewResponse,
    MasteryDistribution,
    MasteryHistoryResponse,
    MasteryTrendsResponse,
    MetacognitiveAlertStudent,
    MetacognitiveAlertsResponse,
    ParagraphAssessmentDetailResponse,
    ParagraphAssessmentStudent,
    SelfAssessmentParagraphSummary,
    SelfAssessmentSummaryResponse,
    StudentSelfAssessmentHistory,
    StudentSelfAssessmentItem,
    StrugglingTopicResponse,
    StudentProgressDetailResponse,
    TeacherClassDetailResponse,
    TeacherClassResponse,
    TeacherDashboardResponse,
)
from app.repositories.self_assessment_repo import SelfAssessmentRepository
from app.services.teacher_analytics.class_analytics_service import ClassAnalyticsService
from app.services.teacher_analytics.mastery_analytics_service import (
    MasteryAnalyticsService,
)
from app.services.teacher_analytics.student_progress_service import (
    StudentProgressService,
)
from app.services.teacher_analytics.teacher_access_service import TeacherAccessService

logger = logging.getLogger(__name__)


class TeacherAnalyticsService:
    """
    Orchestrator service for Teacher Dashboard analytics.

    Delegates to specialized services for:
    - Access control (TeacherAccessService)
    - Mastery calculations (MasteryAnalyticsService)
    - Class analytics (ClassAnalyticsService)
    - Student progress (StudentProgressService)
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self._access = TeacherAccessService(db)
        self._mastery = MasteryAnalyticsService(db)
        self._classes = ClassAnalyticsService(db, self._access, self._mastery)
        self._progress = StudentProgressService(db, self._access)
        self._sa_repo = SelfAssessmentRepository(db)

    # ========================================================================
    # HELPERS
    # ========================================================================

    async def _resolve_student_ids(
        self,
        user_id: int,
        school_id: int,
        class_id: Optional[int] = None,
    ) -> tuple[Optional["Teacher"], List[int], List[int]]:
        """
        Resolve teacher → class_ids → student_ids with optional class_id filter.

        Returns:
            (teacher, class_ids, student_ids) — teacher is None if not found.
        """
        from app.models.teacher import Teacher

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None, [], []

        class_ids = await self._access.get_teacher_class_ids(teacher.id)
        if not class_ids:
            return teacher, [], []

        # Apply class_id filter
        if class_id is not None:
            if class_id not in class_ids:
                return teacher, [], []
            class_ids = [class_id]

        student_ids = await self._access.get_student_ids_for_classes(class_ids)
        return teacher, class_ids, student_ids

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    async def get_dashboard(
        self,
        user_id: int,
        school_id: int
    ) -> TeacherDashboardResponse:
        logger.info(f"Getting dashboard for user {user_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return TeacherDashboardResponse(
                classes_count=0,
                total_students=0,
                students_by_level=MasteryDistribution()
            )

        class_ids = await self._access.get_teacher_class_ids(teacher.id)
        if not class_ids:
            return TeacherDashboardResponse(
                classes_count=0,
                total_students=0,
                students_by_level=MasteryDistribution()
            )

        total_students, distribution, avg_score = (
            await self._mastery.get_dashboard_distribution(class_ids)
        )

        return TeacherDashboardResponse(
            classes_count=len(class_ids),
            total_students=total_students,
            students_by_level=distribution,
            average_class_score=round(avg_score, 1),
            students_needing_help=distribution.level_c,
            recent_activity=[]
        )

    # ========================================================================
    # CLASSES
    # ========================================================================

    async def get_classes(
        self,
        user_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        academic_year: Optional[str] = None,
        grade_level: Optional[int] = None,
    ) -> tuple[List[TeacherClassResponse], int]:
        logger.info(f"Getting classes for user {user_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return [], 0

        return await self._classes.get_classes(
            teacher.id,
            page=page,
            page_size=page_size,
            academic_year=academic_year,
            grade_level=grade_level,
        )

    async def get_class_detail(
        self,
        user_id: int,
        school_id: int,
        class_id: int
    ) -> Optional[TeacherClassDetailResponse]:
        logger.info(f"Getting class detail: class_id={class_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        return await self._classes.get_class_detail(teacher.id, school_id, class_id)

    async def get_class_overview(
        self,
        user_id: int,
        school_id: int,
        class_id: int
    ) -> Optional[ClassOverviewResponse]:
        logger.info(f"Getting class overview: class_id={class_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        classes_list, _ = await self._classes.get_classes(teacher.id)
        class_info = next((c for c in classes_list if c.id == class_id), None)

        if not class_info:
            return None

        return await self._classes.get_class_overview(teacher.id, class_id, class_info)

    # ========================================================================
    # STUDENT PROGRESS
    # ========================================================================

    async def get_student_progress(
        self,
        user_id: int,
        school_id: int,
        class_id: int,
        student_id: int
    ) -> Optional[StudentProgressDetailResponse]:
        logger.info(f"Getting student progress: student_id={student_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        return await self._progress.get_student_progress(
            teacher.id, school_id, class_id, student_id
        )

    async def get_mastery_history(
        self,
        user_id: int,
        school_id: int,
        student_id: int,
        paragraph_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        source_type: Optional[str] = None,
        limit: int = 50,
        offset: int = 0,
    ) -> Optional[MasteryHistoryResponse]:
        logger.info(f"Getting mastery history: student_id={student_id}")

        return await self._progress.get_mastery_history(
            school_id, student_id,
            paragraph_id=paragraph_id,
            chapter_id=chapter_id,
            source_type=source_type,
            limit=limit,
            offset=offset,
        )

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    async def get_analytics_summary(
        self,
        user_id: int,
        school_id: int,
        class_id: Optional[int] = None,
    ) -> AnalyticsSummaryResponse:
        """Get summary metrics for analytics dashboard header."""
        teacher, class_ids, student_ids = await self._resolve_student_ids(
            user_id, school_id, class_id
        )
        if not student_ids:
            return AnalyticsSummaryResponse()

        return await self._mastery.get_analytics_summary(student_ids, class_ids)

    async def get_struggling_topics(
        self,
        user_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
        class_id: Optional[int] = None,
    ) -> tuple[List[StrugglingTopicResponse], int]:
        logger.info(f"Getting struggling topics for user {user_id}")

        teacher, class_ids, student_ids = await self._resolve_student_ids(
            user_id, school_id, class_id
        )
        if not student_ids:
            return [], 0

        return await self._mastery.get_struggling_topics(
            student_ids,
            page=page,
            page_size=page_size,
        )

    async def get_mastery_trends(
        self,
        user_id: int,
        school_id: int,
        period: str = "weekly",
        class_id: Optional[int] = None,
    ) -> MasteryTrendsResponse:
        logger.info(f"Getting mastery trends for user {user_id}, period={period}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            from datetime import datetime, timedelta, timezone
            end_date = datetime.now(timezone.utc).date()
            start_date = end_date - timedelta(days=7 if period == "weekly" else 30)
            return MasteryTrendsResponse(
                period=period,
                start_date=start_date,
                end_date=end_date,
                overall_trend="stable",
                overall_change_percentage=0.0,
                class_trends=[]
            )

        all_class_ids = await self._access.get_teacher_class_ids(teacher.id)

        # Apply class_id filter
        if class_id is not None:
            if class_id not in all_class_ids:
                from datetime import datetime, timedelta, timezone
                end_date = datetime.now(timezone.utc).date()
                start_date = end_date - timedelta(days=7 if period == "weekly" else 30)
                return MasteryTrendsResponse(
                    period=period,
                    start_date=start_date,
                    end_date=end_date,
                    overall_trend="stable",
                    overall_change_percentage=0.0,
                    class_trends=[]
                )
            target_class_ids = [class_id]
        else:
            target_class_ids = all_class_ids

        classes, _ = await self._classes.get_classes(teacher.id)
        classes_data = [
            {"id": c.id, "name": c.name, "average_score": c.average_score}
            for c in classes
            if c.id in target_class_ids
        ]

        # Build student_ids per class for trend calculation
        student_ids_by_class = {}
        for cid in target_class_ids:
            student_ids_by_class[cid] = await self._access.get_student_ids_for_classes([cid])

        return await self._mastery.get_mastery_trends(
            classes_data, student_ids_by_class, period
        )

    # ========================================================================
    # SELF-ASSESSMENT ANALYTICS
    # ========================================================================

    async def get_self_assessment_summary(
        self,
        user_id: int,
        school_id: int,
        class_id: Optional[int] = None,
    ) -> SelfAssessmentSummaryResponse:
        """Get aggregated self-assessment breakdown by paragraph."""
        teacher, class_ids, student_ids = await self._resolve_student_ids(
            user_id, school_id, class_id
        )
        if not student_ids:
            return SelfAssessmentSummaryResponse()

        rows = await self._sa_repo.get_summary_by_paragraph(student_ids)

        paragraphs = []
        total_assessments = 0
        for r in rows:
            total = r["total"]
            total_assessments += total
            paragraphs.append(SelfAssessmentParagraphSummary(
                paragraph_id=r["paragraph_id"],
                paragraph_title=r["paragraph_title"],
                chapter_id=r["chapter_id"],
                chapter_title=r["chapter_title"],
                total_assessments=total,
                understood_count=r["understood"],
                questions_count=r["questions"],
                difficult_count=r["difficult"],
                understood_pct=round(r["understood"] / total * 100, 1) if total else 0,
                questions_pct=round(r["questions"] / total * 100, 1) if total else 0,
                difficult_pct=round(r["difficult"] / total * 100, 1) if total else 0,
            ))

        return SelfAssessmentSummaryResponse(
            total_assessments=total_assessments,
            total_students=len(student_ids),
            paragraphs=paragraphs,
        )

    async def get_metacognitive_alerts(
        self,
        user_id: int,
        school_id: int,
        class_id: Optional[int] = None,
    ) -> MetacognitiveAlertsResponse:
        """Get students with overconfidence/underconfidence patterns."""
        teacher, class_ids, student_ids = await self._resolve_student_ids(
            user_id, school_id, class_id
        )
        if not student_ids:
            return MetacognitiveAlertsResponse()

        overconfident_records, underconfident_records = (
            await self._sa_repo.get_metacognitive_alerts(student_ids)
        )

        from app.models.student import Student
        from app.models.paragraph import Paragraph
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        async def build_alerts(records):
            alerts = []
            for rec in records:
                res = await self.db.execute(
                    select(Student)
                    .options(selectinload(Student.user))
                    .where(Student.id == rec.student_id)
                )
                student = res.scalar_one_or_none()
                if not student or not student.user:
                    continue

                p_res = await self.db.execute(
                    select(Paragraph.title).where(Paragraph.id == rec.paragraph_id)
                )
                p_title = p_res.scalar_one_or_none() or "—"

                alerts.append(MetacognitiveAlertStudent(
                    student_id=student.id,
                    student_code=student.student_code,
                    first_name=student.user.first_name,
                    last_name=student.user.last_name,
                    paragraph_id=rec.paragraph_id,
                    paragraph_title=p_title,
                    rating=rec.rating,
                    practice_score=rec.practice_score,
                    mastery_impact=rec.mastery_impact,
                    created_at=rec.created_at,
                ))
            return alerts

        return MetacognitiveAlertsResponse(
            overconfident=await build_alerts(overconfident_records),
            underconfident=await build_alerts(underconfident_records),
        )

    async def get_paragraph_assessments(
        self,
        user_id: int,
        school_id: int,
        paragraph_id: int,
        class_id: Optional[int] = None,
    ) -> ParagraphAssessmentDetailResponse:
        """Get per-student assessment details for a specific paragraph."""
        teacher, class_ids, student_ids = await self._resolve_student_ids(
            user_id, school_id, class_id
        )
        if not student_ids:
            return ParagraphAssessmentDetailResponse(
                paragraph_id=paragraph_id, paragraph_title="", students=[]
            )

        records = await self._sa_repo.get_assessments_for_paragraph(student_ids, paragraph_id)

        from app.models.student import Student
        from app.models.paragraph import Paragraph
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        # Get paragraph title
        p_res = await self.db.execute(
            select(Paragraph.title).where(Paragraph.id == paragraph_id)
        )
        p_title = p_res.scalar_one_or_none() or ""

        students = []
        for rec in records:
            res = await self.db.execute(
                select(Student)
                .options(selectinload(Student.user))
                .where(Student.id == rec.student_id)
            )
            student = res.scalar_one_or_none()
            if not student or not student.user:
                continue

            students.append(ParagraphAssessmentStudent(
                student_id=student.id,
                first_name=student.user.first_name,
                last_name=student.user.last_name,
                rating=rec.rating,
                practice_score=rec.practice_score,
                mastery_impact=rec.mastery_impact,
                created_at=rec.created_at,
            ))

        # Sort: difficult first, then questions, then understood
        rating_order = {"difficult": 0, "questions": 1, "understood": 2}
        students.sort(key=lambda s: rating_order.get(s.rating, 3))

        return ParagraphAssessmentDetailResponse(
            paragraph_id=paragraph_id,
            paragraph_title=p_title,
            students=students,
        )

    async def get_student_self_assessments(
        self,
        user_id: int,
        school_id: int,
        student_id: int,
    ) -> Optional[StudentSelfAssessmentHistory]:
        """Get self-assessment history for a student (teacher view)."""
        from app.models.student import Student
        from app.models.paragraph import Paragraph
        from app.models.chapter import Chapter
        from sqlalchemy import select
        from sqlalchemy.orm import selectinload

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        res = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.id == student_id)
        )
        student = res.scalar_one_or_none()
        if not student or not student.user:
            return None

        student_name = f"{student.user.last_name} {student.user.first_name}"

        records = await self._sa_repo.get_student_assessments(student_id)

        p_ids = list({r.paragraph_id for r in records})
        p_info = {}
        if p_ids:
            p_res = await self.db.execute(
                select(Paragraph.id, Paragraph.title, Chapter.title.label("chapter_title"))
                .join(Chapter, Chapter.id == Paragraph.chapter_id)
                .where(Paragraph.id.in_(p_ids))
            )
            for row in p_res.all():
                p_info[row.id] = (row.title, row.chapter_title)

        def classify_mismatch(rating: str, practice_score) -> Optional[str]:
            if practice_score is None:
                return None
            if rating == "understood" and practice_score < 60:
                return "overconfident"
            if rating == "difficult" and practice_score > 80:
                return "underconfident"
            return None

        items = []
        adequate = overconfident = underconfident = 0

        for rec in records:
            titles = p_info.get(rec.paragraph_id, ("—", "—"))
            mismatch = classify_mismatch(rec.rating, rec.practice_score)

            if mismatch == "overconfident":
                overconfident += 1
            elif mismatch == "underconfident":
                underconfident += 1
            else:
                adequate += 1

            items.append(StudentSelfAssessmentItem(
                id=rec.id,
                paragraph_id=rec.paragraph_id,
                paragraph_title=titles[0],
                chapter_title=titles[1],
                rating=rec.rating,
                practice_score=rec.practice_score,
                mastery_impact=rec.mastery_impact,
                mismatch_type=mismatch,
                created_at=rec.created_at,
            ))

        return StudentSelfAssessmentHistory(
            student_id=student_id,
            student_name=student_name,
            total_assessments=len(records),
            adequate_count=adequate,
            overconfident_count=overconfident,
            underconfident_count=underconfident,
            assessments=items,
        )
