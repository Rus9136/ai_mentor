"""
Teacher Analytics Service - Orchestrator.

Coordinates specialized services for Teacher Dashboard.
"""

import logging
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.teacher_dashboard import (
    ClassOverviewResponse,
    MasteryDistribution,
    MasteryHistoryResponse,
    MasteryTrendsResponse,
    StrugglingTopicResponse,
    StudentProgressDetailResponse,
    TeacherClassDetailResponse,
    TeacherClassResponse,
    TeacherDashboardResponse,
)
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
        """
        Initialize TeacherAnalyticsService.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self._access = TeacherAccessService(db)
        self._mastery = MasteryAnalyticsService(db)
        self._classes = ClassAnalyticsService(db, self._access, self._mastery)
        self._progress = StudentProgressService(db, self._access)

    # ========================================================================
    # DASHBOARD
    # ========================================================================

    async def get_dashboard(
        self,
        user_id: int,
        school_id: int
    ) -> TeacherDashboardResponse:
        """
        Get teacher dashboard data.

        Args:
            user_id: User ID of the teacher
            school_id: School ID for tenant isolation

        Returns:
            TeacherDashboardResponse with overview stats
        """
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
            recent_activity=[]  # TODO: implement recent activity
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
        """
        Get list of classes for teacher.

        Args:
            user_id: User ID of the teacher
            school_id: School ID
            page: Page number (1-based)
            page_size: Items per page
            academic_year: Optional filter by academic year
            grade_level: Optional filter by grade level (1-11)

        Returns:
            Tuple of (list of TeacherClassResponse, total count)
        """
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
        """
        Get detailed class info with students.

        Args:
            user_id: User ID of the teacher
            school_id: School ID
            class_id: Class ID

        Returns:
            TeacherClassDetailResponse or None
        """
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
        """
        Get class overview with analytics.

        Args:
            user_id: User ID
            school_id: School ID
            class_id: Class ID

        Returns:
            ClassOverviewResponse or None
        """
        logger.info(f"Getting class overview: class_id={class_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        # Get basic class info
        class_response = await self._classes.get_classes(teacher.id)
        class_info = next((c for c in class_response if c.id == class_id), None)

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
        """
        Get detailed student progress.

        Args:
            user_id: Teacher's user ID
            school_id: School ID
            class_id: Class ID (for access verification)
            student_id: Student ID

        Returns:
            StudentProgressDetailResponse or None
        """
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
        student_id: int
    ) -> Optional[MasteryHistoryResponse]:
        """
        Get mastery history timeline for a student.

        Args:
            user_id: Teacher's user ID
            school_id: School ID
            student_id: Student ID

        Returns:
            MasteryHistoryResponse or None
        """
        logger.info(f"Getting mastery history: student_id={student_id}")

        return await self._progress.get_mastery_history(school_id, student_id)

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    async def get_struggling_topics(
        self,
        user_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20,
    ) -> tuple[List[StrugglingTopicResponse], int]:
        """
        Get topics where many students are struggling.

        Args:
            user_id: Teacher's user ID
            school_id: School ID
            page: Page number (1-based)
            page_size: Items per page

        Returns:
            Tuple of (list of StrugglingTopicResponse, total count)
        """
        logger.info(f"Getting struggling topics for user {user_id}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return [], 0

        class_ids = await self._access.get_teacher_class_ids(teacher.id)
        if not class_ids:
            return [], 0

        student_ids = await self._access.get_student_ids_for_classes(class_ids)
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
        period: str = "weekly"
    ) -> MasteryTrendsResponse:
        """
        Get mastery trends across classes.

        Args:
            user_id: Teacher's user ID
            school_id: School ID
            period: "weekly" or "monthly"

        Returns:
            MasteryTrendsResponse
        """
        logger.info(f"Getting mastery trends for user {user_id}, period={period}")

        teacher = await self._access.get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            from datetime import datetime, timedelta
            end_date = datetime.utcnow().date()
            start_date = end_date - timedelta(days=7 if period == "weekly" else 30)
            return MasteryTrendsResponse(
                period=period,
                start_date=start_date,
                end_date=end_date,
                overall_trend="stable",
                overall_change_percentage=0.0,
                class_trends=[]
            )

        classes = await self._classes.get_classes(teacher.id)
        classes_data = [
            {"id": c.id, "name": c.name, "average_score": c.average_score}
            for c in classes
        ]

        return await self._mastery.get_mastery_trends(classes_data, period)
