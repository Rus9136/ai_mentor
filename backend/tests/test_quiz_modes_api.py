"""
Integration tests for Quiz Battle Phase 2.2 API endpoints.

Tests:
- Team Mode: create, join (team assignment), team-leaderboard, results with teams
- Self-Paced: create, next-question, submit-answer, student-progress
- Quick Question: create quick-question session
"""
import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.quiz import QuizSession, QuizParticipant, QuizTeam, QuizSessionStatus
from app.models.user import User
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.test import Test


# ========== Fixtures ==========


@pytest_asyncio.fixture
async def team_quiz_session(
    db_session: AsyncSession,
    school1,
    teacher_user: tuple[User, Teacher],
    test_with_questions: Test,
) -> QuizSession:
    """Create a team mode quiz session with 2 teams."""
    _, teacher = teacher_user
    session = QuizSession(
        school_id=school1.id,
        teacher_id=teacher.id,
        test_id=test_with_questions.id,
        join_code="888222",
        status=QuizSessionStatus.LOBBY,
        settings={
            "time_per_question_ms": 30000,
            "show_leaderboard": True,
            "mode": "team",
            "team_count": 2,
            "show_space_race": True,
        },
        question_count=1,
        current_question_index=-1,
    )
    db_session.add(session)
    await db_session.flush()

    # Create 2 teams
    team_red = QuizTeam(
        quiz_session_id=session.id,
        school_id=school1.id,
        name="Red",
        color="#E53E3E",
    )
    team_blue = QuizTeam(
        quiz_session_id=session.id,
        school_id=school1.id,
        name="Blue",
        color="#3182CE",
    )
    db_session.add_all([team_red, team_blue])
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest_asyncio.fixture
async def selfpaced_quiz_session(
    db_session: AsyncSession,
    school1,
    teacher_user: tuple[User, Teacher],
    test_with_questions: Test,
) -> QuizSession:
    """Create a self-paced quiz session."""
    _, teacher = teacher_user
    session = QuizSession(
        school_id=school1.id,
        teacher_id=teacher.id,
        test_id=test_with_questions.id,
        join_code="777333",
        status=QuizSessionStatus.LOBBY,
        settings={
            "time_per_question_ms": 30000,
            "mode": "self_paced",
            "scoring_mode": "accuracy",
        },
        question_count=1,
        current_question_index=-1,
    )
    db_session.add(session)
    await db_session.commit()
    await db_session.refresh(session)
    return session


@pytest_asyncio.fixture
async def selfpaced_with_participant(
    db_session: AsyncSession,
    selfpaced_quiz_session: QuizSession,
    student_user: tuple[User, Student],
    school1,
) -> tuple[QuizSession, QuizParticipant]:
    """Self-paced quiz in IN_PROGRESS with a participant."""
    _, student = student_user

    selfpaced_quiz_session.status = QuizSessionStatus.IN_PROGRESS
    selfpaced_quiz_session.current_question_index = 0

    participant = QuizParticipant(
        quiz_session_id=selfpaced_quiz_session.id,
        student_id=student.id,
        school_id=school1.id,
    )
    db_session.add(participant)
    await db_session.commit()
    await db_session.refresh(participant)
    return selfpaced_quiz_session, participant


# ========== Team Mode: Create ==========


class TestCreateTeamQuizSession:
    """Tests for POST /api/v1/teachers/quiz-sessions with mode=team."""

    @pytest.mark.asyncio
    async def test_create_team_session_success(
        self, test_app, teacher_token, test_with_questions,
    ):
        """Teacher creates a team quiz → 201 with team settings."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={
                    "test_id": test_with_questions.id,
                    "settings": {
                        "mode": "team",
                        "team_count": 3,
                        "show_space_race": True,
                    },
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["mode"] == "team"
        assert data["settings"]["team_count"] == 3
        assert data["settings"]["show_space_race"] is True
        assert data["question_count"] == 1  # 1 SINGLE_CHOICE question


# ========== Team Mode: Join ==========


class TestJoinTeamQuizSession:
    """Tests for POST /api/v1/students/quiz-sessions/join with team mode."""

    @pytest.mark.asyncio
    async def test_join_team_session_returns_team_info(
        self, test_app, student_token, team_quiz_session,
    ):
        """Student joins team quiz → response includes team assignment."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"join_code": team_quiz_session.join_code},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["mode"] == "team"
        assert data["team_id"] is not None
        assert data["team_name"] in ("Red", "Blue")
        assert data["team_color"] in ("#E53E3E", "#3182CE")


# ========== Team Mode: Team Leaderboard ==========


class TestTeamLeaderboard:
    """Tests for GET /api/v1/teachers/quiz-sessions/{id}/team-leaderboard."""

    @pytest.mark.asyncio
    async def test_team_leaderboard_success(
        self, test_app, teacher_token, team_quiz_session,
    ):
        """Get team leaderboard for team mode session → 200."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{team_quiz_session.id}/team-leaderboard",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2  # Red and Blue teams
        for team in data:
            assert "name" in team
            assert "color" in team
            assert "total_score" in team
            assert "member_count" in team

    @pytest.mark.asyncio
    async def test_team_leaderboard_wrong_mode_400(
        self, test_app, teacher_token, db_session, school1, teacher_user, test_with_questions,
    ):
        """Get team leaderboard for classic session → 400."""
        _, teacher = teacher_user
        classic_session = QuizSession(
            school_id=school1.id,
            teacher_id=teacher.id,
            test_id=test_with_questions.id,
            join_code="666444",
            status=QuizSessionStatus.LOBBY,
            settings={"mode": "classic"},
            question_count=1,
            current_question_index=-1,
        )
        db_session.add(classic_session)
        await db_session.commit()
        await db_session.refresh(classic_session)

        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{classic_session.id}/team-leaderboard",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 400
        assert "Not a team mode" in response.json()["detail"]


# ========== Team Mode: Results with Teams ==========


class TestTeamModeResults:
    """Tests for GET /teachers/quiz-sessions/{id}/results with team mode."""

    @pytest.mark.asyncio
    async def test_results_include_team_leaderboard(
        self, test_app, teacher_token, team_quiz_session,
    ):
        """Team mode results include team_leaderboard."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{team_quiz_session.id}/results",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "team_leaderboard" in data
        assert len(data["team_leaderboard"]) == 2  # Red and Blue


# ========== Self-Paced Mode: Create ==========


class TestCreateSelfPacedSession:
    """Tests for creating self-paced quiz sessions."""

    @pytest.mark.asyncio
    async def test_create_selfpaced_forces_accuracy(
        self, test_app, teacher_token, test_with_questions,
    ):
        """Self-paced mode forces scoring_mode to 'accuracy'."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={
                    "test_id": test_with_questions.id,
                    "settings": {"mode": "self_paced", "scoring_mode": "speed"},
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["settings"]["mode"] == "self_paced"
        # scoring_mode should be forced to accuracy
        assert data["settings"]["scoring_mode"] == "accuracy"


# ========== Self-Paced Mode: Next Question ==========


class TestSelfPacedNextQuestion:
    """Tests for GET /api/v1/students/quiz-sessions/{id}/next-question."""

    @pytest.mark.asyncio
    async def test_get_next_question_success(
        self, test_app, student_token, selfpaced_with_participant,
    ):
        """Student gets next question in self-paced mode → 200."""
        session, _ = selfpaced_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/students/quiz-sessions/{session.id}/next-question",
                headers={"Authorization": f"Bearer {student_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "question" in data
        assert data["answered_count"] == 0
        assert data["total_questions"] == 1
        assert "options" in data["question"]


# ========== Self-Paced Mode: Submit Answer ==========


class TestSelfPacedSubmitAnswer:
    """Tests for POST /api/v1/students/quiz-sessions/{id}/submit-answer."""

    @pytest.mark.asyncio
    async def test_submit_answer_returns_feedback(
        self, test_app, student_token, selfpaced_with_participant,
    ):
        """Submit answer in self-paced mode → immediate feedback with correct_option."""
        session, _ = selfpaced_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                f"/api/v1/students/quiz-sessions/{session.id}/submit-answer",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"question_index": 0, "selected_option": 0},
            )

        assert response.status_code == 200
        data = response.json()
        assert "is_correct" in data
        assert "correct_option" in data
        assert "score" in data
        assert "total_score" in data
        assert "is_finished" in data
        # Score should be 0 or 1000 (accuracy mode)
        assert data["score"] in (0, 1000)


# ========== Self-Paced Mode: Student Progress (Teacher) ==========


class TestStudentProgress:
    """Tests for GET /api/v1/teachers/quiz-sessions/{id}/student-progress."""

    @pytest.mark.asyncio
    async def test_student_progress_success(
        self, test_app, teacher_token, selfpaced_with_participant,
    ):
        """Teacher gets self-paced student progress → 200."""
        session, _ = selfpaced_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{session.id}/student-progress",
                headers={"Authorization": f"Bearer {teacher_token}"},
            )

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1  # One participant
        assert data[0]["answered"] == 0
        assert data[0]["total"] == 1
        assert "student_name" in data[0]

    @pytest.mark.asyncio
    async def test_student_progress_wrong_teacher(
        self, test_app, teacher2_token, selfpaced_with_participant,
    ):
        """Wrong teacher → 403."""
        session, _ = selfpaced_with_participant
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.get(
                f"/api/v1/teachers/quiz-sessions/{session.id}/student-progress",
                headers={"Authorization": f"Bearer {teacher2_token}"},
            )

        assert response.status_code == 403


# ========== Quick Question Mode ==========


class TestCreateQuickQuestion:
    """Tests for POST /api/v1/teachers/quiz-sessions/quick-question."""

    @pytest.mark.asyncio
    async def test_create_quick_question_success(self, test_app, teacher_token):
        """Teacher creates quick question session → 201 without test_id."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/quick-question",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={
                    "question_text": "What is 2 + 2?",
                    "options": ["3", "4", "5", "6"],
                    "time_per_question_ms": 20000,
                },
            )

        assert response.status_code == 201
        data = response.json()
        assert data["test_id"] is None
        assert data["question_count"] == 0
        assert data["settings"]["mode"] == "quick_question"
        assert len(data["join_code"]) == 6

    @pytest.mark.asyncio
    async def test_create_quick_question_no_auth(self, test_app):
        """Create quick question without auth → 401/403."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            response = await client.post(
                "/api/v1/teachers/quiz-sessions/quick-question",
                json={
                    "question_text": "What is 2 + 2?",
                    "options": ["3", "4"],
                },
            )

        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_quick_question_join_and_results(
        self, test_app, teacher_token, student_token,
    ):
        """Quick question: create → student joins → works."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            # Create session
            create_response = await client.post(
                "/api/v1/teachers/quiz-sessions/quick-question",
                headers={"Authorization": f"Bearer {teacher_token}"},
                json={
                    "question_text": "Capital of Kazakhstan?",
                    "options": ["Almaty", "Astana", "Shymkent"],
                },
            )
            assert create_response.status_code == 201
            join_code = create_response.json()["join_code"]

            # Student joins
            join_response = await client.post(
                "/api/v1/students/quiz-sessions/join",
                headers={"Authorization": f"Bearer {student_token}"},
                json={"join_code": join_code},
            )
            assert join_response.status_code == 200
            data = join_response.json()
            assert data["mode"] == "quick_question"
