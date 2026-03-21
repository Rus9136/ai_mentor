"""
Integration tests for Coding AI Mentor (chat for coding challenges).

Tests:
- Session creation and reuse
- System prompt building
- Action message formatting
- Session isolation
- Invalid challenge returns 404
"""
import pytest
import pytest_asyncio

from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.coding import CodingTopic, CodingChallenge
from app.models.school import School
from app.services.coding_chat_service import CodingChatService, SYSTEM_PROMPTS, ACTION_PROMPTS
from app.schemas.coding_chat import CodingAction


STUDENT_BASE = "/api/v1/students"


def auth(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


# =============================================================================
# Fixtures
# =============================================================================

@pytest_asyncio.fixture
async def coding_challenge(db_session: AsyncSession) -> CodingChallenge:
    """Create a topic with one challenge for AI mentor tests."""
    topic = CodingTopic(
        title="AI Test Topic",
        slug="ai-test-topic",
        description="Topic for AI mentor tests",
        sort_order=0,
        is_active=True,
    )
    db_session.add(topic)
    await db_session.flush()

    challenge = CodingChallenge(
        topic_id=topic.id,
        title="Sum Two Numbers",
        title_kk="Екі санның қосындысы",
        description="Read two integers and print their sum.",
        description_kk="Екі бүтін санды оқып, олардың қосындысын шығарыңыз.",
        difficulty="easy",
        sort_order=0,
        points=10,
        starter_code="a = int(input())\nb = int(input())\n",
        test_cases=[
            {"input": "2\n3", "expected_output": "5", "is_hidden": False, "description": "2+3=5"},
        ],
        is_active=True,
    )
    db_session.add(challenge)
    await db_session.commit()

    return challenge


# =============================================================================
# Session Management Tests
# =============================================================================


class TestCodingChatSessionManagement:
    """Test session creation, reuse, and isolation."""

    @pytest.mark.asyncio
    async def test_create_session(
        self, db_session: AsyncSession, student_user, school1: School, coding_challenge
    ):
        """Should create a new coding session for a challenge."""
        _, student = student_user
        service = CodingChatService(db_session)

        session = await service.get_or_create_session(
            student_id=student.id,
            school_id=school1.id,
            challenge_id=coding_challenge.id,
            language="ru",
        )

        assert session is not None
        assert session.session_type == "coding"
        assert session.challenge_id == coding_challenge.id
        assert session.student_id == student.id
        assert session.language == "ru"
        assert session.message_count == 0

    @pytest.mark.asyncio
    async def test_session_reuse(
        self, db_session: AsyncSession, student_user, school1: School, coding_challenge
    ):
        """Second call to get_or_create should return the same session."""
        _, student = student_user
        service = CodingChatService(db_session)

        session1 = await service.get_or_create_session(
            student.id, school1.id, coding_challenge.id, "ru"
        )
        session2 = await service.get_or_create_session(
            student.id, school1.id, coding_challenge.id, "ru"
        )

        assert session1.id == session2.id

    @pytest.mark.asyncio
    async def test_get_session_with_messages(
        self, db_session: AsyncSession, student_user, school1: School, coding_challenge
    ):
        """Should load session with messages via selectinload."""
        _, student = student_user
        service = CodingChatService(db_session)

        session = await service.get_or_create_session(
            student.id, school1.id, coding_challenge.id, "ru"
        )

        loaded = await service.get_session_with_messages(
            session.id, student.id, school1.id
        )
        assert loaded is not None
        assert loaded.id == session.id
        assert hasattr(loaded, 'messages')

    @pytest.mark.asyncio
    async def test_get_challenge_session_empty(
        self, db_session: AsyncSession, student_user, school1: School, coding_challenge
    ):
        """Should return None if no session exists for challenge."""
        _, student = student_user
        service = CodingChatService(db_session)

        result = await service.get_challenge_session(
            coding_challenge.id, student.id, school1.id
        )
        assert result is None

    @pytest.mark.asyncio
    async def test_get_challenge_session_exists(
        self, db_session: AsyncSession, student_user, school1: School, coding_challenge
    ):
        """Should find existing session for challenge."""
        _, student = student_user
        service = CodingChatService(db_session)

        created = await service.get_or_create_session(
            student.id, school1.id, coding_challenge.id, "ru"
        )

        found = await service.get_challenge_session(
            coding_challenge.id, student.id, school1.id
        )
        assert found is not None
        assert found.id == created.id


# =============================================================================
# Prompt Building Tests (pure functions, no DB)
# =============================================================================


class TestPromptBuilding:
    """Test system prompt and action message formatting."""

    def test_system_prompt_ru(self, coding_challenge):
        """Russian system prompt includes challenge title and description."""
        service = CodingChatService.__new__(CodingChatService)
        prompt = service._build_system_prompt(coding_challenge, "ru")

        assert "Sum Two Numbers" in prompt
        assert "Read two integers" in prompt
        assert "НИКОГДА не давай готовое решение" in prompt

    def test_system_prompt_kk(self, coding_challenge):
        """Kazakh system prompt uses kk title and description."""
        service = CodingChatService.__new__(CodingChatService)
        prompt = service._build_system_prompt(coding_challenge, "kk")

        assert "Екі санның қосындысы" in prompt
        assert "ЕШҚАШАН дайын шешімді" in prompt

    def test_format_hint_message(self, coding_challenge):
        """Hint action message includes student code."""
        service = CodingChatService.__new__(CodingChatService)
        msg = service._format_action_message(
            CodingAction.HINT, "x = 5\nprint(x)", "ru"
        )

        assert "x = 5" in msg
        assert "подсказк" in msg.lower()

    def test_format_explain_error_message(self, coding_challenge):
        """Explain error message includes error traceback."""
        service = CodingChatService.__new__(CodingChatService)
        msg = service._format_action_message(
            CodingAction.EXPLAIN_ERROR, "print(x)", "ru",
            error="NameError: name 'x' is not defined"
        )

        assert "NameError" in msg
        assert "print(x)" in msg

    def test_format_code_review_message(self, coding_challenge):
        """Code review message includes code and test results."""
        service = CodingChatService.__new__(CodingChatService)
        msg = service._format_action_message(
            CodingAction.CODE_REVIEW, "a=1\nb=2\nprint(a+b)", "ru",
            test_results="1/1 tests passed"
        )

        assert "a=1" in msg
        assert "1/1 tests passed" in msg

    def test_format_step_by_step_message(self, coding_challenge):
        """Step-by-step message includes code."""
        service = CodingChatService.__new__(CodingChatService)
        msg = service._format_action_message(
            CodingAction.STEP_BY_STEP, "x = 5\ny = 3", "kk"
        )

        assert "x = 5" in msg

    def test_code_truncation(self, coding_challenge):
        """Very long code gets truncated to prevent token abuse."""
        service = CodingChatService.__new__(CodingChatService)
        long_code = "x = 1\n" * 1000  # ~6000 chars
        msg = service._format_action_message(
            CodingAction.HINT, long_code, "ru"
        )

        # Should be truncated to 3000 chars max
        assert len(msg) < 5000

    def test_llm_messages_structure(self, coding_challenge):
        """LLM messages array should have system + user."""
        from unittest.mock import MagicMock

        service = CodingChatService.__new__(CodingChatService)

        mock_session = MagicMock()
        mock_session.messages = []

        messages = service._build_llm_messages(
            mock_session, "System prompt here", "User message here"
        )

        assert len(messages) == 2
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt here"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User message here"


# =============================================================================
# API Endpoint Tests
# =============================================================================


class TestCodingAIEndpoints:
    """Test API endpoints (non-streaming)."""

    @pytest.mark.asyncio
    async def test_invalid_challenge_404(self, test_app, student_token):
        """Non-existent challenge returns 404."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"{STUDENT_BASE}/coding/ai/start",
                headers=auth(student_token),
                json={
                    "challenge_id": 99999,
                    "action": "hint",
                    "code": "x = 1",
                },
            )

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_invalid_action_422(self, test_app, student_token):
        """Invalid action type returns 422."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"{STUDENT_BASE}/coding/ai/start",
                headers=auth(student_token),
                json={
                    "challenge_id": 1,
                    "action": "invalid_action",
                    "code": "x = 1",
                },
            )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_missing_code_422(self, test_app, student_token):
        """Missing code field returns 422."""
        async with AsyncClient(
            transport=ASGITransport(app=test_app), base_url="http://test"
        ) as client:
            resp = await client.post(
                f"{STUDENT_BASE}/coding/ai/start",
                headers=auth(student_token),
                json={
                    "challenge_id": 1,
                    "action": "hint",
                },
            )

        assert resp.status_code == 422
