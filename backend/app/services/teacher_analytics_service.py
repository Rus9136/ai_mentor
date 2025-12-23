"""
Teacher Analytics Service для Teacher Dashboard.

Итерация 11: Реализация аналитики для учителей.
- Dashboard статистика по классам учителя
- Распределение A/B/C по ученикам
- Прогресс отдельных учеников
- Аналитика по struggling topics
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.orm import selectinload

from app.models.teacher import Teacher
from app.models.student import Student
from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent
from app.models.class_teacher import ClassTeacher
from app.models.mastery import ParagraphMastery, ChapterMastery, MasteryHistory
from app.models.test_attempt import TestAttempt
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.schemas.teacher_dashboard import (
    MasteryDistribution,
    StudentWithMastery,
    TeacherDashboardResponse,
    TeacherClassResponse,
    TeacherClassDetailResponse,
    ClassOverviewResponse,
    StudentProgressDetailResponse,
    ChapterProgressBrief,
    TestAttemptBrief,
    MasteryHistoryItem,
    MasteryHistoryResponse,
    StrugglingTopicResponse,
    ClassTrend,
    MasteryTrendsResponse,
    RecentActivityItem,
    StudentBriefResponse,
)

logger = logging.getLogger(__name__)


class TeacherAnalyticsService:
    """Service for Teacher Dashboard analytics."""

    def __init__(self, db: AsyncSession):
        """
        Initialize TeacherAnalyticsService.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    async def _get_teacher_by_user_id(
        self,
        user_id: int,
        school_id: int
    ) -> Optional[Teacher]:
        """Get teacher record by user_id."""
        result = await self.db.execute(
            select(Teacher)
            .options(selectinload(Teacher.classes))
            .where(
                and_(
                    Teacher.user_id == user_id,
                    Teacher.school_id == school_id,
                    Teacher.is_deleted == False
                )
            )
        )
        return result.scalar_one_or_none()

    async def _get_teacher_class_ids(self, teacher_id: int) -> List[int]:
        """Get list of class IDs for teacher."""
        result = await self.db.execute(
            select(ClassTeacher.class_id)
            .where(ClassTeacher.teacher_id == teacher_id)
        )
        return [row[0] for row in result.fetchall()]

    async def _verify_teacher_access_to_class(
        self,
        teacher_id: int,
        class_id: int
    ) -> bool:
        """Verify teacher has access to the class."""
        result = await self.db.execute(
            select(ClassTeacher)
            .where(
                and_(
                    ClassTeacher.teacher_id == teacher_id,
                    ClassTeacher.class_id == class_id
                )
            )
        )
        return result.scalar_one_or_none() is not None

    async def _get_class_students(self, class_id: int) -> List[Student]:
        """Get students in a class."""
        result = await self.db.execute(
            select(Student)
            .join(ClassStudent, ClassStudent.student_id == Student.id)
            .options(selectinload(Student.user))
            .where(
                and_(
                    ClassStudent.class_id == class_id,
                    Student.is_deleted == False
                )
            )
        )
        return list(result.scalars().all())

    def _calculate_mastery_distribution(
        self,
        students_mastery: List[Dict[str, Any]]
    ) -> MasteryDistribution:
        """Calculate A/B/C distribution from student mastery data."""
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

        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return TeacherDashboardResponse(
                classes_count=0,
                total_students=0,
                students_by_level=MasteryDistribution()
            )

        class_ids = await self._get_teacher_class_ids(teacher.id)

        if not class_ids:
            return TeacherDashboardResponse(
                classes_count=0,
                total_students=0,
                students_by_level=MasteryDistribution()
            )

        # Get total students count
        students_result = await self.db.execute(
            select(func.count(func.distinct(ClassStudent.student_id)))
            .where(ClassStudent.class_id.in_(class_ids))
        )
        total_students = students_result.scalar() or 0

        # Get mastery distribution across all students
        mastery_result = await self.db.execute(
            select(ChapterMastery.mastery_level, func.count(func.distinct(ChapterMastery.student_id)))
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

        # Calculate average score
        avg_result = await self.db.execute(
            select(func.avg(ChapterMastery.mastery_score))
            .join(ClassStudent, ClassStudent.student_id == ChapterMastery.student_id)
            .where(ClassStudent.class_id.in_(class_ids))
        )
        avg_score = avg_result.scalar() or 0.0

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
        school_id: int
    ) -> List[TeacherClassResponse]:
        """
        Get list of classes for teacher.

        Args:
            user_id: User ID of the teacher
            school_id: School ID

        Returns:
            List of TeacherClassResponse
        """
        logger.info(f"Getting classes for user {user_id}")

        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return []

        # Get classes with student counts
        result = await self.db.execute(
            select(SchoolClass)
            .join(ClassTeacher, ClassTeacher.class_id == SchoolClass.id)
            .options(selectinload(SchoolClass.students))
            .where(
                and_(
                    ClassTeacher.teacher_id == teacher.id,
                    SchoolClass.is_deleted == False
                )
            )
            .order_by(SchoolClass.grade_level, SchoolClass.name)
        )

        classes = list(result.scalars().all())
        response = []

        for cls in classes:
            # Get mastery distribution for class
            student_ids = [s.id for s in cls.students if not s.is_deleted]

            distribution = MasteryDistribution()
            avg_score = 0.0
            progress = 0

            if student_ids:
                # Get mastery levels
                mastery_result = await self.db.execute(
                    select(ChapterMastery.mastery_level, func.count())
                    .where(ChapterMastery.student_id.in_(student_ids))
                    .group_by(ChapterMastery.mastery_level)
                )

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

                # Get average score
                avg_result = await self.db.execute(
                    select(func.avg(ChapterMastery.mastery_score))
                    .where(ChapterMastery.student_id.in_(student_ids))
                )
                avg_score = avg_result.scalar() or 0.0

                # Get average progress
                progress_result = await self.db.execute(
                    select(func.avg(ChapterMastery.progress_percentage))
                    .where(ChapterMastery.student_id.in_(student_ids))
                )
                progress = int(progress_result.scalar() or 0)

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

        return response

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

        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        # Verify access
        if not await self._verify_teacher_access_to_class(teacher.id, class_id):
            logger.warning(f"Teacher {teacher.id} does not have access to class {class_id}")
            return None

        # Get class
        result = await self.db.execute(
            select(SchoolClass)
            .where(
                and_(
                    SchoolClass.id == class_id,
                    SchoolClass.school_id == school_id,
                    SchoolClass.is_deleted == False
                )
            )
        )
        cls = result.scalar_one_or_none()
        if not cls:
            return None

        # Get students
        students = await self._get_class_students(class_id)
        student_ids = [s.id for s in students]

        # Get mastery data for students
        students_with_mastery = []

        for student in students:
            # Get latest chapter mastery
            mastery_result = await self.db.execute(
                select(ChapterMastery)
                .where(ChapterMastery.student_id == student.id)
                .order_by(desc(ChapterMastery.updated_at))
                .limit(1)
            )
            mastery = mastery_result.scalar_one_or_none()

            # Get progress stats
            progress_result = await self.db.execute(
                select(
                    func.count(ParagraphMastery.id).filter(ParagraphMastery.is_completed == True),
                    func.count(ParagraphMastery.id)
                )
                .where(ParagraphMastery.student_id == student.id)
            )
            completed, total = progress_result.fetchone() or (0, 0)

            students_with_mastery.append(StudentWithMastery(
                id=student.id,
                student_code=student.student_code,
                first_name=student.user.first_name if student.user else "",
                last_name=student.user.last_name if student.user else "",
                middle_name=student.user.middle_name if student.user else None,
                mastery_level=mastery.mastery_level if mastery else None,
                mastery_score=mastery.mastery_score if mastery else None,
                completed_paragraphs=completed,
                total_paragraphs=total,
                progress_percentage=int(100 * completed / total) if total > 0 else 0,
                last_activity=mastery.updated_at if mastery else None
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

        # Calculate average
        scores = [sm.mastery_score for sm in students_with_mastery if sm.mastery_score is not None]
        avg_score = sum(scores) / len(scores) if scores else 0.0

        # Calculate progress
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

        # Get basic class info
        class_response = await self.get_classes(user_id, school_id)
        class_info = next((c for c in class_response if c.id == class_id), None)

        if not class_info:
            return None

        # Get chapters progress (aggregate across students)
        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        students = await self._get_class_students(class_id)
        student_ids = [s.id for s in students]

        chapters_progress = []

        if student_ids:
            # Get unique chapters from mastery data
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

        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return None

        # Verify access
        if not await self._verify_teacher_access_to_class(teacher.id, class_id):
            return None

        # Get student
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    Student.is_deleted == False
                )
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return None

        # Get class name
        class_result = await self.db.execute(
            select(SchoolClass.name)
            .where(SchoolClass.id == class_id)
        )
        class_name = class_result.scalar() or "Unknown"

        # Get chapters progress
        chapters_result = await self.db.execute(
            select(
                Chapter.id,
                Chapter.title,
                Chapter.number,
                ChapterMastery.mastery_level,
                ChapterMastery.mastery_score,
                ChapterMastery.completed_paragraphs,
                ChapterMastery.total_paragraphs,
                ChapterMastery.progress_percentage
            )
            .join(ChapterMastery, ChapterMastery.chapter_id == Chapter.id)
            .where(ChapterMastery.student_id == student_id)
            .order_by(Chapter.number)
        )

        chapters_progress = []
        overall_score = 0.0
        overall_level = None

        for row in chapters_result.fetchall():
            ch_id, title, number, level, score, completed, total, progress = row
            chapters_progress.append(ChapterProgressBrief(
                chapter_id=ch_id,
                chapter_title=title,
                chapter_number=number,
                mastery_level=level,
                mastery_score=score,
                completed_paragraphs=completed or 0,
                total_paragraphs=total or 0,
                progress_percentage=progress or 0
            ))
            if score:
                overall_score = max(overall_score, score)
                overall_level = level

        # Get recent tests
        tests_result = await self.db.execute(
            select(TestAttempt)
            .options(selectinload(TestAttempt.test))
            .where(
                and_(
                    TestAttempt.student_id == student_id,
                    TestAttempt.status == "completed"
                )
            )
            .order_by(desc(TestAttempt.completed_at))
            .limit(10)
        )

        recent_tests = []
        for attempt in tests_result.scalars().all():
            recent_tests.append(TestAttemptBrief(
                id=attempt.id,
                test_id=attempt.test_id,
                test_title=attempt.test.title if attempt.test else "Unknown",
                score=attempt.score * attempt.max_score,
                max_score=attempt.max_score,
                percentage=attempt.score * 100,
                completed_at=attempt.completed_at
            ))

        # Get total time spent
        time_result = await self.db.execute(
            select(func.sum(ParagraphMastery.time_spent))
            .where(ParagraphMastery.student_id == student_id)
        )
        total_time = time_result.scalar() or 0

        # Get last activity
        last_activity_result = await self.db.execute(
            select(func.max(ParagraphMastery.last_updated_at))
            .where(ParagraphMastery.student_id == student_id)
        )
        last_activity = last_activity_result.scalar()

        days_since = 0
        if last_activity:
            days_since = (datetime.utcnow() - last_activity).days

        return StudentProgressDetailResponse(
            student=StudentBriefResponse(
                id=student.id,
                student_code=student.student_code,
                grade_level=student.grade_level,
                first_name=student.user.first_name if student.user else "",
                last_name=student.user.last_name if student.user else "",
                middle_name=student.user.middle_name if student.user else None
            ),
            class_name=class_name,
            overall_mastery_level=overall_level,
            overall_mastery_score=overall_score,
            total_time_spent=total_time,
            chapters_progress=chapters_progress,
            recent_tests=recent_tests,
            last_activity=last_activity,
            days_since_last_activity=days_since
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

        # Get student
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(
                and_(
                    Student.id == student_id,
                    Student.school_id == school_id,
                    Student.is_deleted == False
                )
            )
        )
        student = result.scalar_one_or_none()
        if not student:
            return None

        # Get history
        history_result = await self.db.execute(
            select(MasteryHistory)
            .where(MasteryHistory.student_id == student_id)
            .order_by(desc(MasteryHistory.recorded_at))
            .limit(50)
        )

        history = []
        for h in history_result.scalars().all():
            history.append(MasteryHistoryItem(
                id=h.id,
                recorded_at=h.recorded_at,
                previous_level=h.previous_level,
                new_level=h.new_level,
                previous_score=h.previous_score,
                new_score=h.new_score,
                chapter_id=h.chapter_id,
                paragraph_id=h.paragraph_id,
                test_attempt_id=h.test_attempt_id
            ))

        student_name = f"{student.user.first_name} {student.user.last_name}" if student.user else "Unknown"

        return MasteryHistoryResponse(
            student_id=student_id,
            student_name=student_name,
            history=history
        )

    # ========================================================================
    # ANALYTICS
    # ========================================================================

    async def get_struggling_topics(
        self,
        user_id: int,
        school_id: int
    ) -> List[StrugglingTopicResponse]:
        """
        Get topics where many students are struggling.

        Args:
            user_id: Teacher's user ID
            school_id: School ID

        Returns:
            List of StrugglingTopicResponse
        """
        logger.info(f"Getting struggling topics for user {user_id}")

        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return []

        class_ids = await self._get_teacher_class_ids(teacher.id)
        if not class_ids:
            return []

        # Get student IDs in teacher's classes
        students_result = await self.db.execute(
            select(func.distinct(ClassStudent.student_id))
            .where(ClassStudent.class_id.in_(class_ids))
        )
        student_ids = [row[0] for row in students_result.fetchall()]

        if not student_ids:
            return []

        # Get paragraphs with struggling stats
        result = await self.db.execute(
            select(
                Paragraph.id,
                Paragraph.title,
                Chapter.id,
                Chapter.title,
                func.count(ParagraphMastery.id).filter(ParagraphMastery.status == "struggling"),
                func.count(ParagraphMastery.id),
                func.avg(ParagraphMastery.average_score)
            )
            .join(ParagraphMastery, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Chapter.id == Paragraph.chapter_id)
            .where(ParagraphMastery.student_id.in_(student_ids))
            .group_by(Paragraph.id, Paragraph.title, Chapter.id, Chapter.title)
            .having(func.count(ParagraphMastery.id).filter(ParagraphMastery.status == "struggling") > 0)
            .order_by(desc(func.count(ParagraphMastery.id).filter(ParagraphMastery.status == "struggling")))
            .limit(20)
        )

        topics = []
        for row in result.fetchall():
            para_id, para_title, ch_id, ch_title, struggling, total, avg_score = row
            topics.append(StrugglingTopicResponse(
                paragraph_id=para_id,
                paragraph_title=para_title,
                chapter_id=ch_id,
                chapter_title=ch_title,
                struggling_count=struggling,
                total_students=total,
                struggling_percentage=round(100 * struggling / total, 1) if total > 0 else 0.0,
                average_score=round((avg_score or 0) * 100, 1)
            ))

        return topics

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

        # Calculate date range
        end_date = datetime.utcnow().date()
        if period == "weekly":
            start_date = end_date - timedelta(days=7)
        else:
            start_date = end_date - timedelta(days=30)

        teacher = await self._get_teacher_by_user_id(user_id, school_id)
        if not teacher:
            return MasteryTrendsResponse(
                period=period,
                start_date=start_date,
                end_date=end_date,
                overall_trend="stable",
                overall_change_percentage=0.0,
                class_trends=[]
            )

        classes = await self.get_classes(user_id, school_id)

        class_trends = []
        total_change = 0.0

        for cls in classes:
            # Get average scores at start and end of period
            # Simplified: just return current average as "current" and 0 change
            class_trends.append(ClassTrend(
                class_id=cls.id,
                class_name=cls.name,
                previous_average=cls.average_score,
                current_average=cls.average_score,
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
