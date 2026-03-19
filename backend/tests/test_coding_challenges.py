"""
Integration tests for Coding Challenges module.

Tests:
- Schema validation
- Service logic (XP, status, attempt counting)
- API endpoints
"""
import pytest
import pytest_asyncio
from datetime import datetime, timezone

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select as sa_select

from app.models.coding import CodingTopic, CodingChallenge, CodingSubmission
from app.models.user import User
from app.models.student import Student
from app.models.school import School
from app.models.teacher import Teacher
from app.models.school_class import SchoolClass
from app.models.class_student import ClassStudent
from app.schemas.coding import SubmissionCreate


STUDENT_BASE = "/api/v1/students"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Fixtures
# =============================================================================


@pytest_asyncio.fixture
async def coding_data(
    db_session: AsyncSession,
    school1: School,
) -> tuple[CodingTopic, CodingChallenge]:
    """Create a topic with one challenge."""
    topic = CodingTopic(
        title="Variables",
        title_kk="Айнымалылар",
        slug="test-variables",
        description="Basics",
        sort_order=0,
        icon="Variable",
        grade_level=6,
        is_active=True,
    )
    db_session.add(topic)
    await db_session.flush()

    challenge = CodingChallenge(
        topic_id=topic.id,
        title="Hello World",
        title_kk="Сәлем Әлем",
        description='Print "Hello, World!"',
        difficulty="easy",
        sort_order=0,
        points=10,
        starter_code='# Write your code\n',
        hints=["Use print()"],
        hints_kk=["print() қолданыңыз"],
        test_cases=[
            {
                "input": "",
                "expected_output": "Hello, World!",
                "is_hidden": False,
                "description": "Basic test",
            },
            {
                "input": "",
                "expected_output": "Hello, World!",
                "is_hidden": True,
                "description": "Hidden test",
            },
        ],
        time_limit_ms=5000,
        is_active=True,
    )
    db_session.add(challenge)
    await db_session.commit()

    return topic, challenge


# =============================================================================
# Schema Tests
# =============================================================================


class TestSubmissionCreateSchema:
    def test_valid_submission(self):
        data = SubmissionCreate(code='print("hi")', tests_passed=1, tests_total=1)
        assert data.code == 'print("hi")'
        assert data.tests_passed == 1

    def test_empty_code_fails(self):
        with pytest.raises(Exception):
            SubmissionCreate(code="", tests_passed=1, tests_total=1)

    def test_negative_tests_fails(self):
        with pytest.raises(Exception):
            SubmissionCreate(code="x=1", tests_passed=-1, tests_total=1)


# =============================================================================
# API Tests
# =============================================================================


class TestCodingTopicsAPI:
    @pytest.mark.asyncio
    async def test_list_topics(
        self, test_app, student_token, coding_data
    ):
        topic, _ = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/topics",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert isinstance(data, list)
        assert len(data) >= 1
        found = [t for t in data if t["slug"] == "test-variables"]
        assert len(found) == 1
        assert found[0]["total_challenges"] == 1
        assert found[0]["solved_challenges"] == 0


class TestCodingChallengesAPI:
    @pytest.mark.asyncio
    async def test_list_challenges(
        self, test_app, student_token, coding_data
    ):
        topic, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/topics/test-variables/challenges",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 1
        assert data[0]["title"] == "Hello World"
        assert data[0]["status"] == "not_started"

    @pytest.mark.asyncio
    async def test_get_challenge_detail(
        self, test_app, student_token, coding_data
    ):
        _, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.get(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Hello World"
        assert data["difficulty"] == "easy"
        assert data["points"] == 10
        assert len(data["test_cases"]) == 2
        # Hidden test should not expose expected_output
        hidden = [tc for tc in data["test_cases"] if tc["is_hidden"]]
        assert hidden[0]["expected_output"] == ""

    @pytest.mark.asyncio
    async def test_submit_passed(
        self, test_app, student_token, coding_data
    ):
        _, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={
                    "code": 'print("Hello, World!")',
                    "tests_passed": 2,
                    "tests_total": 2,
                },
                headers=auth(student_token),
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "passed"
        assert data["xp_earned"] == 10
        assert data["attempt_number"] == 1

    @pytest.mark.asyncio
    async def test_submit_failed_then_passed(
        self, test_app, student_token, coding_data
    ):
        _, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # First attempt: failed
            resp1 = await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={
                    "code": 'print("wrong")',
                    "tests_passed": 0,
                    "tests_total": 2,
                },
                headers=auth(student_token),
            )
            assert resp1.status_code == 201
            assert resp1.json()["status"] == "failed"
            assert resp1.json()["xp_earned"] == 0
            assert resp1.json()["attempt_number"] == 1

            # Second attempt: passed
            resp2 = await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={
                    "code": 'print("Hello, World!")',
                    "tests_passed": 2,
                    "tests_total": 2,
                },
                headers=auth(student_token),
            )
            assert resp2.status_code == 201
            assert resp2.json()["status"] == "passed"
            assert resp2.json()["xp_earned"] == 10
            assert resp2.json()["attempt_number"] == 2

    @pytest.mark.asyncio
    async def test_no_double_xp(
        self, test_app, student_token, coding_data
    ):
        """XP should only be awarded once per challenge."""
        _, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # First pass
            resp1 = await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={
                    "code": 'print("Hello, World!")',
                    "tests_passed": 2,
                    "tests_total": 2,
                },
                headers=auth(student_token),
            )
            assert resp1.json()["xp_earned"] == 10

            # Second pass — no XP
            resp2 = await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={
                    "code": 'print("Hello, World!")',
                    "tests_passed": 2,
                    "tests_total": 2,
                },
                headers=auth(student_token),
            )
            assert resp2.json()["xp_earned"] == 0

    @pytest.mark.asyncio
    async def test_submissions_history(
        self, test_app, student_token, coding_data
    ):
        _, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Submit twice
            await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={"code": "x=1", "tests_passed": 0, "tests_total": 2},
                headers=auth(student_token),
            )
            await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={"code": 'print("Hello, World!")', "tests_passed": 2, "tests_total": 2},
                headers=auth(student_token),
            )

            # Get history
            resp = await client.get(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submissions",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        # Most recent first
        assert data[0]["attempt_number"] == 2

    @pytest.mark.asyncio
    async def test_stats(
        self, test_app, student_token, coding_data
    ):
        _, challenge = coding_data

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Solve a challenge
            await client.post(
                f"{STUDENT_BASE}/coding/challenges/{challenge.id}/submit",
                json={"code": 'print("Hello, World!")', "tests_passed": 2, "tests_total": 2},
                headers=auth(student_token),
            )

            resp = await client.get(
                f"{STUDENT_BASE}/coding/stats",
                headers=auth(student_token),
            )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total_solved"] == 1
        assert data["total_xp"] == 10
