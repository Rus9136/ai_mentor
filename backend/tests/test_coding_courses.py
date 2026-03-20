"""
Integration tests for Coding Courses (Learning Paths) module.

Tests:
- Course listing with progress
- Lesson listing with completion status
- Lesson detail with optional challenge
- Lesson completion (progress tracking)
- Course completion detection
"""
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import (
    CodingTopic,
    CodingChallenge,
    CodingCourse,
    CodingLesson,
    CodingCourseProgress,
)
from app.models.user import User
from app.models.student import Student


STUDENT_BASE = "/api/v1/students"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def course_data(
    db_session: AsyncSession,
) -> tuple[CodingCourse, list[CodingLesson], CodingChallenge]:
    """Create a course with 3 lessons, one linked to a challenge."""
    # First create a topic + challenge for lesson linking
    topic = CodingTopic(
        title="Test Topic",
        slug="test-course-topic",
        sort_order=0,
        is_active=True,
    )
    db_session.add(topic)
    await db_session.flush()

    challenge = CodingChallenge(
        topic_id=topic.id,
        title="Linked Challenge",
        description="A challenge linked to a lesson",
        difficulty="easy",
        sort_order=0,
        points=10,
        test_cases=[
            {"input": "", "expected_output": "Hello", "is_hidden": False, "description": "test"},
        ],
        is_active=True,
    )
    db_session.add(challenge)
    await db_session.flush()

    # Create course
    course = CodingCourse(
        title="Test Course",
        title_kk="Тест курсы",
        description="A test course",
        slug="test-course",
        grade_level=6,
        total_lessons=3,
        estimated_hours=2.0,
        sort_order=0,
        icon="BookOpen",
        is_active=True,
    )
    db_session.add(course)
    await db_session.flush()

    # Create 3 lessons
    lessons = []
    for i, (title, has_challenge) in enumerate([
        ("Lesson 1: Intro", False),
        ("Lesson 2: Practice", True),
        ("Lesson 3: Summary", False),
    ]):
        lesson = CodingLesson(
            course_id=course.id,
            title=title,
            sort_order=i,
            theory_content=f"Theory for {title}",
            challenge_id=challenge.id if has_challenge else None,
            is_active=True,
        )
        db_session.add(lesson)
        lessons.append(lesson)

    await db_session.commit()

    # Refresh to get IDs
    for lesson in lessons:
        await db_session.refresh(lesson)

    return course, lessons, challenge


# =============================================================================
# API Tests — Courses
# =============================================================================


class TestCodingCoursesAPI:
    @pytest.mark.asyncio
    async def test_list_courses(self, test_app, student_token, course_data):
        course, _, _ = course_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        found = [c for c in data if c["slug"] == "test-course"]
        assert len(found) == 1
        assert found[0]["total_lessons"] == 3
        assert found[0]["completed_lessons"] == 0
        assert found[0]["started"] is False
        assert found[0]["completed"] is False

    @pytest.mark.asyncio
    async def test_list_lessons(self, test_app, student_token, course_data):
        course, lessons, _ = course_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses/test-course/lessons",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["title"] == "Lesson 1: Intro"
        assert data[0]["is_completed"] is False
        assert data[1]["has_challenge"] is True
        assert data[2]["has_challenge"] is False

    @pytest.mark.asyncio
    async def test_list_lessons_not_found(self, test_app, student_token):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses/nonexistent/lessons",
                headers=auth(student_token),
            )

        assert resp.status_code == 404


# =============================================================================
# API Tests — Lesson Detail
# =============================================================================


class TestLessonDetailAPI:
    @pytest.mark.asyncio
    async def test_get_lesson_without_challenge(
        self, test_app, student_token, course_data
    ):
        _, lessons, _ = course_data
        lesson = lessons[0]  # No challenge

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses/lessons/{lesson.id}",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Lesson 1: Intro"
        assert data["theory_content"] == "Theory for Lesson 1: Intro"
        assert data["challenge_id"] is None
        assert data["challenge"] is None
        assert data["is_completed"] is False

    @pytest.mark.asyncio
    async def test_get_lesson_with_challenge(
        self, test_app, student_token, course_data
    ):
        _, lessons, challenge = course_data
        lesson = lessons[1]  # Has challenge

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses/lessons/{lesson.id}",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Lesson 2: Practice"
        assert data["challenge_id"] == challenge.id
        assert data["challenge"] is not None
        assert data["challenge"]["title"] == "Linked Challenge"

    @pytest.mark.asyncio
    async def test_get_nonexistent_lesson(self, test_app, student_token):
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses/lessons/99999",
                headers=auth(student_token),
            )

        assert resp.status_code == 404


# =============================================================================
# API Tests — Lesson Completion
# =============================================================================


class TestLessonCompletionAPI:
    @pytest.mark.asyncio
    async def test_complete_first_lesson(
        self, test_app, student_token, course_data
    ):
        course, lessons, _ = course_data
        lesson = lessons[0]

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"{STUDENT_BASE}/coding/courses/lessons/{lesson.id}/complete",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["lesson_id"] == lesson.id
        assert data["course_id"] == course.id
        assert data["completed_lessons"] == 1
        assert data["total_lessons"] == 3
        assert data["course_completed"] is False

    @pytest.mark.asyncio
    async def test_complete_all_lessons(
        self, test_app, student_token, course_data
    ):
        course, lessons, _ = course_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Complete all 3 lessons in order
            for i, lesson in enumerate(lessons):
                resp = await client.post(
                    f"{STUDENT_BASE}/coding/courses/lessons/{lesson.id}/complete",
                    headers=auth(student_token),
                )
                assert resp.status_code == 200

            data = resp.json()
            assert data["completed_lessons"] == 3
            assert data["course_completed"] is True

    @pytest.mark.asyncio
    async def test_complete_same_lesson_twice_idempotent(
        self, test_app, student_token, course_data
    ):
        _, lessons, _ = course_data
        lesson = lessons[0]

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp1 = await client.post(
                f"{STUDENT_BASE}/coding/courses/lessons/{lesson.id}/complete",
                headers=auth(student_token),
            )
            resp2 = await client.post(
                f"{STUDENT_BASE}/coding/courses/lessons/{lesson.id}/complete",
                headers=auth(student_token),
            )

        assert resp1.status_code == 200
        assert resp2.status_code == 200
        # Both return same count (idempotent)
        assert resp1.json()["completed_lessons"] == resp2.json()["completed_lessons"]

    @pytest.mark.asyncio
    async def test_progress_shows_in_course_list(
        self, test_app, student_token, course_data
    ):
        course, lessons, _ = course_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Complete first lesson
            await client.post(
                f"{STUDENT_BASE}/coding/courses/lessons/{lessons[0].id}/complete",
                headers=auth(student_token),
            )

            # Check course list
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        found = [c for c in data if c["slug"] == "test-course"]
        assert len(found) == 1
        assert found[0]["completed_lessons"] == 1
        assert found[0]["started"] is True
        assert found[0]["completed"] is False

    @pytest.mark.asyncio
    async def test_lesson_shows_completed_in_list(
        self, test_app, student_token, course_data
    ):
        _, lessons, _ = course_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Complete first lesson
            await client.post(
                f"{STUDENT_BASE}/coding/courses/lessons/{lessons[0].id}/complete",
                headers=auth(student_token),
            )

            # Check lessons list
            resp = await client.get(
                f"{STUDENT_BASE}/coding/courses/test-course/lessons",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["is_completed"] is True
        assert data[1]["is_completed"] is False
        assert data[2]["is_completed"] is False
