"""
Integration tests for Quiz Battle API endpoints.

- POST /api/v1/teachers/quiz-sessions (create)
- GET /api/v1/teachers/quiz-sessions (list)
- PATCH /api/v1/teachers/quiz-sessions/{id}/start
- PATCH /api/v1/teachers/quiz-sessions/{id}/cancel
- GET /api/v1/teachers/quiz-sessions/{id}/results
- POST /api/v1/students/quiz-sessions/join
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizSession, QuizParticipant, QuizSessionStatus
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.test import Test


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def quiz_session(
    db_session: AsyncSession,
    school1,
    teacher_user: tuple[User, Teacher],
    test_with_questions: Test,
) -> QuizSession:
    """Create a quiz session in LOBBY status."""
    _, teacher = teacher_user
    session = QuizSession(
        school_id=school1.id,
        teacher_id=teacher.id,
        test_id=test_with_questions.id,
        join_code="999111",
        status=QuizSessionStatus.LOBBY,
        settings={"time_per_question_ms": 30000, "show_leaderboard": True},
        question_count=1,  # Only 1 SINGLE_CHOICE question in test_with_questions
        current_question_index=-1,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest_asyncio.fixture
async def quiz_with_participant(
    db_session: AsyncSession,
    quiz_session: QuizSession,
    student_user: tuple[User, Student],
    school1,
) -> tuple[QuizSession, QuizParticipant]:
    """Add a participant to the quiz session."""
    _, student = student_user
    participant = QuizParticipant(
        quiz_session_id=quiz_session.id,
        student_id=student.id,
        school_id=school1.id,
    )
    db_session.add(participant)
    await db_session.commit()
    await db_session.refresh(participant)
    return quiz_session, participant


# ========== Teacher: POST /teachers/quiz-sessions ==========


class TestCreateQuizSession:
    """Tests for POST /api/v1/teachers/quiz-sessions."""

    @pytest.mark.asyncio
    async def test_create_session_success(
        self, test_app, teacher_token, test_with_questions
    ):
        """Teacher creates a quiz session → 201 with join_code."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={"test_id": test_with_questions.id},
            )

        assert response.status_code == 201
        data = response.json()
        assert "join_code" in data
        assert len(data["join_code"]) == 6
        assert data["status"] == "lobby"
        assert data["question_count"] == 1  # Only 1 SINGLE_CHOICE in fixture

    @pytest.mark.asyncio
    async def test_create_session_invalid_test(self, test_app, teacher_token):
        """Create session with nonexistent test → 400."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={"test_id": 99999},
            )

        assert response.status_code == 400

    @pytest.mark.asyncio
    async def test_create_session_no_auth(self, test_app, test_with_questions):
        """Create session without auth → 401/403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/",
                json={"test_id": test_with_questions.id},
            )

        assert response.status_code in (401, 403)


# ========== Teacher: GET /teachers/quiz-sessions ==========


class TestListQuizSessions:
    """Tests for GET /api/v1/teachers/quiz-sessions."""

    @pytest.mark.asyncio
    async def test_list_sessions(self, test_app, teacher_token, quiz_session):
        """Teacher lists their sessions."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) >= 1
        assert data[0]["join_code"] == "999111"

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, test_app, teacher_token):
        """Teacher with no sessions → empty list."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        assert response.json() == []


# ========== Student: POST /students/quiz-sessions/join ==========


class TestJoinQuizSession:
    """Tests for POST /api/v1/students/quiz-sessions/join."""

    @pytest.mark.asyncio
    async def test_join_success(self, test_app, student_token, quiz_session):
        """Student joins with valid code → 200."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"join_code": quiz_session.join_code},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["quiz_session_id"] == quiz_session.id
        assert data["status"] == "lobby"
        assert data["participant_count"] == 1

    @pytest.mark.asyncio
    async def test_join_invalid_code(self, test_app, student_token):
        """Student joins with invalid code → 400."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"join_code": "000000"},
            )

        assert response.status_code == 400
        assert "Invalid" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_join_wrong_school(
        self, test_app, student2_token, quiz_session
    ):
        """Student from different school → 400."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                headers={"Authorization": f"Bearer {student2_token}"},
                json={"join_code": quiz_session.join_code},
            )

        assert response.status_code == 400
        assert "different school" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_join_no_auth(self, test_app, quiz_session):
        """Join without auth → 401/403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                json={"join_code": quiz_session.join_code},
            )

        assert response.status_code in (401, 403)


# ========== Teacher: PATCH /teachers/quiz-sessions/{id}/start ==========


class TestStartQuiz:
    """Tests for PATCH /api/v1/teachers/quiz-sessions/{id}/start."""

    @pytest.mark.asyncio
    async def test_start_success(
        self, test_app, teacher_token, quiz_with_participant
    ):
        """Start quiz with participants → 200."""
        session, _ = quiz_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/teachers/quiz-sessions/{session.id}/start",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "in_progress"

    @pytest.mark.asyncio
    async def test_start_no_participants(
        self, test_app, teacher_token, quiz_session
    ):
        """Start quiz without participants → 400."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/teachers/quiz-sessions/{quiz_session.id}/start",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 400
        assert "No participants" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_start_wrong_teacher(
        self, test_app, teacher2_token, quiz_with_participant
    ):
        """Start quiz by wrong teacher → 400."""
        session, _ = quiz_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/teachers/quiz-sessions/{session.id}/start",
                headers={"Authorization": f"Bearer {teacher2_token}"},
            )

        assert response.status_code == 400


# ========== Teacher: PATCH /teachers/quiz-sessions/{id}/cancel ==========


class TestCancelQuiz:
    """Tests for PATCH /api/v1/teachers/quiz-sessions/{id}/cancel."""

    @pytest.mark.asyncio
    async def test_cancel_success(self, test_app, teacher_token, quiz_session):
        """Cancel lobby session → 200."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/teachers/quiz-sessions/{quiz_session.id}/cancel",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        assert response.json()["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled(
        self, test_app, teacher_token, quiz_session, db_session
    ):
        """Cancel already cancelled session → 400."""
        quiz_session.status = QuizSessionStatus.CANCELLED
        await db_session.commit()

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.patch(
                f"/api/v1/teachers/quiz-sessions/{quiz_session.id}/cancel",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 400


# ========== Teacher: GET /teachers/quiz-sessions/{id}/results ==========


class TestGetQuizResults:
    """Tests for GET /api/v1/teachers/quiz-sessions/{id}/results."""

    @pytest.mark.asyncio
    async def test_get_results_success(
        self, test_app, teacher_token, quiz_with_participant
    ):
        """Get results for session with participants → 200."""
        session, _ = quiz_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{session.id}/results",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["quiz_session_id"] == session.id
        assert data["total_questions"] == session.question_count
        assert len(data["leaderboard"]) == 1

    @pytest.mark.asyncio
    async def test_get_results_not_found(self, test_app, teacher_token):
        """Get results for nonexistent session → 404."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                "/api/v1/teachers/quiz-sessions/99999/results",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_get_results_wrong_teacher(
        self, test_app, teacher2_token, quiz_with_participant
    ):
        """Get results by wrong teacher → 403."""
        session, _ = quiz_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{session.id}/results",
                headers={"Authorization": f"Bearer {teacher2_token}"},
            )

        assert response.status_code == 403
