"""
Integration tests for coding gamification (Этап 5).

Tests:
1. Solving a challenge → XP lands in student.total_xp
2. Solving a challenge → streak updates
3. Solving first challenge → achievement first_challenge earned
4. Repeat solve → no duplicate XP via gamification
5. Course completion → achievement progress updates
6. Daily quest solve_challenge → increment + completion
"""
import pytest
import pytest_asyncio
from datetime import date

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select, func

from app.models.coding import (
    CodingTopic,
    CodingChallenge,
    CodingSubmission,
    CodingCourse,
    CodingLesson,
    CodingCourseProgress,
)
from app.models.gamification import (
    Achievement,
    StudentAchievement,
    XpTransaction,
    XpSourceType,
    DailyQuest,
    StudentDailyQuest,
    QuestType,
)
from app.models.student import Student
from app.models.school import School
from app.services.coding_service import CodingService, CourseService
from app.schemas.coding import SubmissionCreate


# ═══════════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════════


@pytest_asyncio.fixture
async def coding_topic(db_session: AsyncSession) -> CodingTopic:
    topic = CodingTopic(
        title="Loops",
        title_kk="Циклдар",
        slug="loops",
        description="Loop challenges",
        sort_order=0,
        icon="Loop",
        is_active=True,
    )
    db_session.add(topic)
    await db_session.flush()
    return topic


@pytest_asyncio.fixture
async def coding_challenge(
    db_session: AsyncSession, coding_topic: CodingTopic
) -> CodingChallenge:
    ch = CodingChallenge(
        topic_id=coding_topic.id,
        title="Sum numbers",
        title_kk="Сандарды қосу",
        description="Sum 1 to N",
        difficulty="easy",
        sort_order=0,
        points=15,
        test_cases=[
            {"input": "5", "expected_output": "15", "is_hidden": False},
        ],
        is_active=True,
    )
    db_session.add(ch)
    await db_session.flush()
    return ch


@pytest_asyncio.fixture
async def first_challenge_achievement(db_session: AsyncSession) -> Achievement:
    a = Achievement(
        code="first_challenge",
        name_kk="Бірінші есеп",
        name_ru="Первая задача",
        icon="🎯",
        category="milestone",
        criteria={"type": "challenges_solved", "threshold": 1},
        xp_reward=20,
        rarity="common",
        sort_order=30,
        is_active=True,
    )
    db_session.add(a)
    await db_session.flush()
    return a


@pytest_asyncio.fixture
async def course_graduate_achievement(db_session: AsyncSession) -> Achievement:
    a = Achievement(
        code="course_graduate",
        name_kk="Курс түлегі",
        name_ru="Выпускник курса",
        icon="🎓",
        category="milestone",
        criteria={"type": "courses_completed", "threshold": 1},
        xp_reward=150,
        rarity="epic",
        sort_order=39,
        is_active=True,
    )
    db_session.add(a)
    await db_session.flush()
    return a


@pytest_asyncio.fixture
async def solve_challenge_quest(db_session: AsyncSession) -> DailyQuest:
    q = DailyQuest(
        code="solve_1_challenge",
        name_kk="Python есебін шеш",
        name_ru="Реши задачу по Python",
        quest_type=QuestType.SOLVE_CHALLENGE,
        target_value=1,
        xp_reward=50,
        is_active=True,
    )
    db_session.add(q)
    await db_session.flush()
    return q


@pytest_asyncio.fixture
async def course_with_lessons(
    db_session: AsyncSession, coding_challenge: CodingChallenge
) -> tuple[CodingCourse, list[CodingLesson]]:
    course = CodingCourse(
        title="Python Basics",
        title_kk="Python негіздері",
        slug="python-basics",
        total_lessons=2,
        sort_order=0,
        is_active=True,
    )
    db_session.add(course)
    await db_session.flush()

    lesson1 = CodingLesson(
        course_id=course.id,
        title="Lesson 1",
        title_kk="Сабақ 1",
        sort_order=0,
        theory_content="Intro to Python",
        is_active=True,
    )
    lesson2 = CodingLesson(
        course_id=course.id,
        title="Lesson 2",
        title_kk="Сабақ 2",
        sort_order=1,
        theory_content="Loops",
        challenge_id=coding_challenge.id,
        is_active=True,
    )
    db_session.add_all([lesson1, lesson2])
    await db_session.flush()

    return course, [lesson1, lesson2]


# ═══════════════════════════════════════════════════════════════════════
# Tests
# ═══════════════════════════════════════════════════════════════════════


class TestCodingXP:
    """Test 1: Solving a challenge → XP goes into student.total_xp."""

    @pytest.mark.asyncio
    async def test_solve_awards_xp_to_student(
        self,
        db_session: AsyncSession,
        student_user,
        school1: School,
        coding_challenge: CodingChallenge,
        first_challenge_achievement: Achievement,
    ):
        _, student = student_user
        initial_xp = student.total_xp or 0

        svc = CodingService(db_session)
        data = SubmissionCreate(
            code="print(sum(range(1,6)))",
            tests_passed=1,
            tests_total=1,
            execution_time_ms=500,
        )
        resp = await svc.submit_solution(
            challenge_id=coding_challenge.id,
            student_id=student.id,
            school_id=school1.id,
            data=data,
        )

        assert resp.status == "passed"
        assert resp.xp_earned == 15

        # Check student.total_xp increased (coding XP + streak XP + achievement XP)
        await db_session.refresh(student)
        assert student.total_xp > initial_xp

        # Verify xp_transaction with source_type=coding_challenge exists
        result = await db_session.execute(
            sa_select(XpTransaction).where(
                XpTransaction.student_id == student.id,
                XpTransaction.source_type == XpSourceType.CODING_CHALLENGE,
            )
        )
        txn = result.scalar_one_or_none()
        assert txn is not None
        assert txn.amount == 15
        assert txn.source_id == coding_challenge.id


class TestCodingStreak:
    """Test 2: Solving a challenge → streak updates."""

    @pytest.mark.asyncio
    async def test_solve_updates_streak(
        self,
        db_session: AsyncSession,
        student_user,
        school1: School,
        coding_challenge: CodingChallenge,
        first_challenge_achievement: Achievement,
    ):
        _, student = student_user
        assert (student.current_streak or 0) == 0

        svc = CodingService(db_session)
        data = SubmissionCreate(
            code="print(sum(range(1,6)))",
            tests_passed=1,
            tests_total=1,
        )
        await svc.submit_solution(
            challenge_id=coding_challenge.id,
            student_id=student.id,
            school_id=school1.id,
            data=data,
        )

        await db_session.refresh(student)
        assert student.current_streak >= 1
        assert student.last_activity_date == date.today()


class TestCodingAchievements:
    """Test 3: First challenge solved → achievement first_challenge earned."""

    @pytest.mark.asyncio
    async def test_first_challenge_achievement(
        self,
        db_session: AsyncSession,
        student_user,
        school1: School,
        coding_challenge: CodingChallenge,
        first_challenge_achievement: Achievement,
    ):
        _, student = student_user

        svc = CodingService(db_session)
        data = SubmissionCreate(
            code="print(sum(range(1,6)))",
            tests_passed=1,
            tests_total=1,
        )
        await svc.submit_solution(
            challenge_id=coding_challenge.id,
            student_id=student.id,
            school_id=school1.id,
            data=data,
        )

        # Check StudentAchievement earned
        result = await db_session.execute(
            sa_select(StudentAchievement).where(
                StudentAchievement.student_id == student.id,
                StudentAchievement.achievement_id == first_challenge_achievement.id,
            )
        )
        sa = result.scalar_one_or_none()
        assert sa is not None
        assert sa.is_earned is True
        assert sa.progress == 1.0


class TestNoDuplicateXP:
    """Test 4: Solving same challenge again → no duplicate gamification XP."""

    @pytest.mark.asyncio
    async def test_no_duplicate_gamification_xp(
        self,
        db_session: AsyncSession,
        student_user,
        school1: School,
        coding_challenge: CodingChallenge,
        first_challenge_achievement: Achievement,
    ):
        _, student = student_user

        svc = CodingService(db_session)
        data = SubmissionCreate(
            code="print(sum(range(1,6)))",
            tests_passed=1,
            tests_total=1,
        )

        # First solve
        resp1 = await svc.submit_solution(
            challenge_id=coding_challenge.id,
            student_id=student.id,
            school_id=school1.id,
            data=data,
        )
        assert resp1.xp_earned == 15

        # Second solve — no XP
        resp2 = await svc.submit_solution(
            challenge_id=coding_challenge.id,
            student_id=student.id,
            school_id=school1.id,
            data=data,
        )
        assert resp2.xp_earned == 0

        # Count coding_challenge xp transactions — should be exactly 1
        result = await db_session.execute(
            sa_select(func.count(XpTransaction.id)).where(
                XpTransaction.student_id == student.id,
                XpTransaction.source_type == XpSourceType.CODING_CHALLENGE,
            )
        )
        assert result.scalar() == 1


class TestCourseCompletion:
    """Test 5: Course completion → gamification hook fires."""

    @pytest.mark.asyncio
    async def test_course_completed_awards_xp(
        self,
        db_session: AsyncSession,
        student_user,
        school1: School,
        course_with_lessons,
        course_graduate_achievement: Achievement,
    ):
        _, student = student_user
        course, lessons = course_with_lessons
        initial_xp = student.total_xp or 0

        svc = CourseService(db_session)

        # Complete both lessons
        await svc.complete_lesson(lessons[0].id, student.id, school_id=school1.id)
        resp = await svc.complete_lesson(lessons[1].id, student.id, school_id=school1.id)
        assert resp.course_completed is True

        # Verify course_complete XP transaction
        result = await db_session.execute(
            sa_select(XpTransaction).where(
                XpTransaction.student_id == student.id,
                XpTransaction.source_type == XpSourceType.COURSE_COMPLETE,
            )
        )
        txn = result.scalar_one_or_none()
        assert txn is not None
        assert txn.amount == 100

        # Achievement progress should show earned
        result = await db_session.execute(
            sa_select(StudentAchievement).where(
                StudentAchievement.student_id == student.id,
                StudentAchievement.achievement_id == course_graduate_achievement.id,
            )
        )
        sa = result.scalar_one_or_none()
        assert sa is not None
        assert sa.is_earned is True


class TestDailyQuest:
    """Test 6: Daily quest solve_challenge → increment + completion."""

    @pytest.mark.asyncio
    async def test_quest_incremented_on_solve(
        self,
        db_session: AsyncSession,
        student_user,
        school1: School,
        coding_challenge: CodingChallenge,
        solve_challenge_quest: DailyQuest,
        first_challenge_achievement: Achievement,
    ):
        _, student = student_user

        # Assign quest for today
        today = date.today()
        sdq = StudentDailyQuest(
            student_id=student.id,
            quest_id=solve_challenge_quest.id,
            school_id=school1.id,
            quest_date=today,
        )
        db_session.add(sdq)
        await db_session.flush()

        svc = CodingService(db_session)
        data = SubmissionCreate(
            code="print(sum(range(1,6)))",
            tests_passed=1,
            tests_total=1,
        )
        await svc.submit_solution(
            challenge_id=coding_challenge.id,
            student_id=student.id,
            school_id=school1.id,
            data=data,
        )

        # Quest should be completed (target_value=1, solved 1)
        await db_session.refresh(sdq)
        assert sdq.current_value >= 1
        assert sdq.is_completed is True

        # Daily quest XP transaction should exist
        result = await db_session.execute(
            sa_select(XpTransaction).where(
                XpTransaction.student_id == student.id,
                XpTransaction.source_type == XpSourceType.DAILY_QUEST,
            )
        )
        txn = result.scalar_one_or_none()
        assert txn is not None
        assert txn.amount == 50
