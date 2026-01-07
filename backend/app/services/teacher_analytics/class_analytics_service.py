"""
Class Analytics Service.

Handles class-level analytics for teacher dashboard.
"""

import logging
from typing import List, Optional, Tuple

from sqlalchemy import and_, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chapter import Chapter
from app.models.class_teacher import ClassTeacher
from app.models.mastery import ChapterMastery, ParagraphMastery
from app.models.school_class import SchoolClass
from app.schemas.teacher_dashboard import (
    ChapterProgressBrief,
    ClassOverviewResponse,
    MasteryDistribution,
    StudentWithMastery,
    TeacherClassDetailResponse,
    TeacherClassResponse,
)
from app.services.teacher_analytics.mastery_analytics_service import (
    MasteryAnalyticsService,
)
from app.services.teacher_analytics.teacher_access_service import TeacherAccessService

logger = logging.getLogger(__name__)


class ClassAnalyticsService:
    """Service for class-level analytics."""

    def __init__(
        self,
        db: AsyncSession,
        access_service: TeacherAccessService,
        mastery_service: MasteryAnalyticsService
    ):
        self.db = db
        self._access = access_service
        self._mastery = mastery_service

    async def get_classes(
        self,
        teacher_id: int,
        page: int = 1,
        page_size: int = 20,
        academic_year: Optional[str] = None,
        grade_level: Optional[int] = None,
    ) -> Tuple[List[TeacherClassResponse], int]:
        """
        Get list of classes for teacher with analytics.

        Args:
            teacher_id: Teacher ID
            page: Page number (1-based)
            page_size: Items per page
            academic_year: Optional filter by academic year
            grade_level: Optional filter by grade level (1-11)

        Returns:
            Tuple of (list of TeacherClassResponse, total count)
        """
        # Build conditions
        conditions = [
            ClassTeacher.teacher_id == teacher_id,
            SchoolClass.is_deleted == False  # noqa: E712
        ]

        if academic_year is not None:
            conditions.append(SchoolClass.academic_year == academic_year)
        if grade_level is not None:
            conditions.append(SchoolClass.grade_level == grade_level)

        # Get total count
        count_query = (
            select(func.count())
            .select_from(SchoolClass)
            .join(ClassTeacher, ClassTeacher.class_id == SchoolClass.id)
            .where(and_(*conditions))
        )
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get classes with students (paginated)
        offset = (page - 1) * page_size
        result = await self.db.execute(
            select(SchoolClass)
            .join(ClassTeacher, ClassTeacher.class_id == SchoolClass.id)
            .options(selectinload(SchoolClass.students))
            .where(and_(*conditions))
            .order_by(SchoolClass.grade_level, SchoolClass.name)
            .offset(offset)
            .limit(page_size)
        )

        classes = list(result.scalars().all())
        response = []

        for cls in classes:
            student_ids = [s.id for s in cls.students if not s.is_deleted]

            distribution = MasteryDistribution()
            avg_score = 0.0
            progress = 0

            if student_ids:
                distribution = await self._mastery.get_mastery_distribution_for_students(
                    student_ids
                )
                avg_score = await self._mastery.get_average_score_for_students(
                    student_ids
                )
                progress = await self._mastery.get_average_progress_for_students(
                    student_ids
                )

            response.append(TeacherClassResponse(
                id=cls.id,
                name=cls.name,
                code=cls.code,
                grade_level=cls.grade_level,
                academic_year=cls.academic_year,
                students_count=len(student_ids),
                mastery_distribution=distribution,
                average_score=round(avg_score, 1),
                progress_percentage=progress
            ))

        return response, total

    async def get_class_detail(
        self,
        teacher_id: int,
        school_id: int,
        class_id: int
    ) -> Optional[TeacherClassDetailResponse]:
        """
        Get detailed class info with students and mastery data.

        Args:
            teacher_id: Teacher ID
            school_id: School ID
            class_id: Class ID

        Returns:
            TeacherClassDetailResponse or None
        """
        # Verify access
        if not await self._access.verify_teacher_access_to_class(teacher_id, class_id):
            logger.warning(
                f"Teacher {teacher_id} does not have access to class {class_id}"
            )
            return None

        # Get class
        result = await self.db.execute(
            select(SchoolClass)
            .where(
                and_(
                    SchoolClass.id == class_id,
                    SchoolClass.school_id == school_id,
                    SchoolClass.is_deleted == False  # noqa: E712
                )
            )
        )
        cls = result.scalar_one_or_none()
        if not cls:
            return None

        # Get students
        students = await self._access.get_class_students(class_id)
        student_ids = [s.id for s in students]

        # Batch load mastery data to avoid N+1
        mastery_data = await self._get_students_mastery_data(student_ids)
        progress_data = await self._get_students_progress_data(student_ids)

        # Build students with mastery
        students_with_mastery = []
        for student in students:
            mastery = mastery_data.get(student.id)
            progress = progress_data.get(student.id, (0, 0))

            students_with_mastery.append(StudentWithMastery(
                id=student.id,
                student_code=student.student_code,
                first_name=student.user.first_name if student.user else "",
                last_name=student.user.last_name if student.user else "",
                middle_name=student.user.middle_name if student.user else None,
                mastery_level=mastery["level"] if mastery else None,
                mastery_score=mastery["score"] if mastery else None,
                completed_paragraphs=progress[0],
                total_paragraphs=progress[1],
                progress_percentage=int(100 * progress[0] / progress[1]) if progress[1] > 0 else 0,
                last_activity=mastery["updated_at"] if mastery else None
            ))

        # Calculate distribution
        distribution = MasteryDistribution()
        for sm in students_with_mastery:
            if sm.mastery_level == "A":
                distribution.level_a += 1
            elif sm.mastery_level == "B":
                distribution.level_b += 1
            elif sm.mastery_level == "C":
                distribution.level_c += 1
            else:
                distribution.not_started += 1

        # Calculate averages
        scores = [sm.mastery_score for sm in students_with_mastery if sm.mastery_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        progresses = [sm.progress_percentage for sm in students_with_mastery]
        avg_progress = int(sum(progresses) / len(progresses)) if progresses else 0

        return TeacherClassDetailResponse(
            id=cls.id,
            name=cls.name,
            code=cls.code,
            grade_level=cls.grade_level,
            academic_year=cls.academic_year,
            students_count=len(students),
            mastery_distribution=distribution,
            average_score=round(avg_score, 1),
            progress_percentage=avg_progress,
            students=students_with_mastery
        )

    async def get_class_overview(
        self,
        teacher_id: int,
        class_id: int,
        class_info: TeacherClassResponse
    ) -> Optional[ClassOverviewResponse]:
        """
        Get class overview with chapter analytics.

        Args:
            teacher_id: Teacher ID
            class_id: Class ID
            class_info: Basic class info

        Returns:
            ClassOverviewResponse or None
        """
        # Verify access
        if not await self._access.verify_teacher_access_to_class(teacher_id, class_id):
            return None

        students = await self._access.get_class_students(class_id)
        student_ids = [s.id for s in students]

        chapters_progress = []

        if student_ids:
            # Get chapters progress aggregated across students
            chapters_result = await self.db.execute(
                select(
                    Chapter.id,
                    Chapter.title,
                    Chapter.number,
                    func.avg(ChapterMastery.mastery_score),
                    func.avg(ChapterMastery.progress_percentage)
                )
                .join(ChapterMastery, ChapterMastery.chapter_id == Chapter.id)
                .where(ChapterMastery.student_id.in_(student_ids))
                .group_by(Chapter.id, Chapter.title, Chapter.number)
                .order_by(Chapter.number)
            )

            for row in chapters_result.fetchall():
                chapter_id, title, number, avg_score, avg_progress = row
                level = "A" if avg_score >= 85 else ("B" if avg_score >= 60 else "C")

                chapters_progress.append(ChapterProgressBrief(
                    chapter_id=chapter_id,
                    chapter_title=title,
                    chapter_number=number,
                    mastery_level=level,
                    mastery_score=round(avg_score, 1) if avg_score else 0.0,
                    progress_percentage=int(avg_progress or 0)
                ))

        return ClassOverviewResponse(
            class_info=class_info,
            chapters_progress=chapters_progress,
            trend="stable",
            trend_percentage=0.0
        )

    async def _get_students_mastery_data(
        self,
        student_ids: List[int]
    ) -> dict:
        """
        Batch load latest mastery data for students.

        Args:
            student_ids: List of student IDs

        Returns:
            Dict mapping student_id to mastery data
        """
        if not student_ids:
            return {}

        # Get latest mastery per student using window function
        subquery = (
            select(
                ChapterMastery.student_id,
                ChapterMastery.mastery_level,
                ChapterMastery.mastery_score,
                ChapterMastery.updated_at,
                func.row_number().over(
                    partition_by=ChapterMastery.student_id,
                    order_by=desc(ChapterMastery.updated_at)
                ).label("rn")
            )
            .where(ChapterMastery.student_id.in_(student_ids))
            .subquery()
        )

        result = await self.db.execute(
            select(
                subquery.c.student_id,
                subquery.c.mastery_level,
                subquery.c.mastery_score,
                subquery.c.updated_at
            )
            .where(subquery.c.rn == 1)
        )

        return {
            row[0]: {
                "level": row[1],
                "score": row[2],
                "updated_at": row[3]
            }
            for row in result.fetchall()
        }

    async def _get_students_progress_data(
        self,
        student_ids: List[int]
    ) -> dict:
        """
        Batch load progress data for students.

        Args:
            student_ids: List of student IDs

        Returns:
            Dict mapping student_id to (completed, total) tuple
        """
        if not student_ids:
            return {}

        result = await self.db.execute(
            select(
                ParagraphMastery.student_id,
                func.count(ParagraphMastery.id).filter(
                    ParagraphMastery.is_completed
                ),
                func.count(ParagraphMastery.id)
            )
            .where(ParagraphMastery.student_id.in_(student_ids))
            .group_by(ParagraphMastery.student_id)
        )

        return {
            row[0]: (row[1], row[2])
            for row in result.fetchall()
        }
