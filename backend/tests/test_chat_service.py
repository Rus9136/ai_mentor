"""
Tests for ChatService.

Covers:
- Session management (create, list, get, delete)
- Message handling (send_message, build_llm_messages, get_system_prompt)
- System prompt management (CRUD operations)
- Edge cases (unicode, long content, error handling)
"""

import json
import pytest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch, PropertyMock
from typing import List, Optional

from app.services.chat_service import ChatService, DEFAULT_PROMPTS
from app.services.llm_service import LLMResponse
from app.services.rag_service import RetrievedContext
from app.models.chat import ChatSession, ChatMessage, ChatSessionType
from app.models.system_prompt import SystemPromptTemplate
from app.schemas.chat import SystemPromptCreate, SystemPromptUpdate
from app.schemas.rag import Citation


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def mock_db():
    """Mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_rag_service():
    """Mock RAGService."""
    rag = AsyncMock()
    rag.get_student_mastery_level = AsyncMock(return_value="B")
    rag.retrieve_context = AsyncMock(return_value=RetrievedContext(
        chunks=[],
        total_chars=0,
        paragraph_ids=set()
    ))
    rag._build_context_string = MagicMock(return_value="")
    rag._extract_citations = MagicMock(return_value=[])
    return rag


@pytest.fixture
def mock_llm_service():
    """Mock LLMService."""
    llm = AsyncMock()
    llm.generate = AsyncMock(return_value=LLMResponse(
        content="Test AI response",
        model="test-model",
        tokens_used=100
    ))
    return llm


@pytest.fixture
def chat_service(mock_db, mock_rag_service, mock_llm_service):
    """Create ChatService with mocked dependencies."""
    service = ChatService(mock_db)
    service.rag_service = mock_rag_service
    service.llm = mock_llm_service
    return service


@pytest.fixture
def sample_chat_session():
    """Create a sample ChatSession object."""
    session = MagicMock(spec=ChatSession)
    session.id = 1
    session.student_id = 10
    session.school_id = 5
    session.session_type = "general_tutor"
    session.paragraph_id = None
    session.chapter_id = None
    session.test_id = None
    session.title = "Test Chat Session"
    session.mastery_level = "B"
    session.language = "ru"
    session.message_count = 0
    session.total_tokens_used = 0
    session.last_message_at = None
    session.created_at = datetime.utcnow()
    session.is_deleted = False
    session.messages = []
    return session


@pytest.fixture
def sample_chat_message():
    """Create a sample ChatMessage object."""
    message = MagicMock(spec=ChatMessage)
    message.id = 1
    message.session_id = 1
    message.school_id = 5
    message.role = "user"
    message.content = "Hello, can you help me?"
    message.citations_json = None
    message.context_chunks_used = None
    message.tokens_used = None
    message.model_used = None
    message.processing_time_ms = None
    message.created_at = datetime.utcnow()
    message.is_deleted = False
    return message


@pytest.fixture
def sample_system_prompt():
    """Create a sample SystemPromptTemplate object."""
    prompt = MagicMock(spec=SystemPromptTemplate)
    prompt.id = 1
    prompt.prompt_type = "general_tutor"
    prompt.mastery_level = "B"
    prompt.language = "ru"
    prompt.name = "General Tutor B"
    prompt.description = "Prompt for B-level students"
    prompt.prompt_text = "You are a helpful tutor..."
    prompt.is_active = True
    prompt.version = 1
    prompt.created_at = datetime.utcnow()
    prompt.updated_at = datetime.utcnow()
    return prompt


# =============================================================================
# Session Management Tests
# =============================================================================

class TestCreateSession:
    """Tests for ChatService.create_session method."""

    @pytest.mark.asyncio
    async def test_create_session_success(self, chat_service, mock_db):
        """Test successful session creation."""
        # Setup mock for refresh
        created_session = MagicMock(spec=ChatSession)
        created_session.id = 1
        mock_db.refresh = AsyncMock(side_effect=lambda obj: setattr(obj, 'id', 1))

        result = await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor"
        )

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        chat_service.rag_service.get_student_mastery_level.assert_called_once_with(
            student_id=10,
            school_id=5,
            chapter_id=None
        )

    @pytest.mark.asyncio
    async def test_create_session_with_paragraph_context(self, chat_service, mock_db):
        """Test session creation with paragraph context."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="reading_help",
            paragraph_id=100,
            chapter_id=50
        )

        # Verify mastery level was fetched with chapter_id
        chat_service.rag_service.get_student_mastery_level.assert_called_once_with(
            student_id=10,
            school_id=5,
            chapter_id=50
        )

        # Verify session was added to DB
        mock_db.add.assert_called_once()
        added_session = mock_db.add.call_args[0][0]
        assert added_session.paragraph_id == 100
        assert added_session.chapter_id == 50

    @pytest.mark.asyncio
    async def test_create_session_with_test_context(self, chat_service, mock_db):
        """Test session creation with test context."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="test_help",
            test_id=25
        )

        mock_db.add.assert_called_once()
        added_session = mock_db.add.call_args[0][0]
        assert added_session.test_id == 25
        assert added_session.session_type == "test_help"

    @pytest.mark.asyncio
    async def test_create_session_custom_title(self, chat_service, mock_db):
        """Test session creation with custom title."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor",
            title="My Custom Chat"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.title == "My Custom Chat"

    @pytest.mark.asyncio
    async def test_create_session_auto_generate_title(self, chat_service, mock_db):
        """Test session creation auto-generates title when not provided."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="reading_help"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.title is not None
        assert "Помощь с чтением" in added_session.title

    @pytest.mark.asyncio
    async def test_create_session_kazakh_language(self, chat_service, mock_db):
        """Test session creation with Kazakh language."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor",
            language="kk"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.language == "kk"

    @pytest.mark.asyncio
    async def test_create_session_stores_mastery_level(self, chat_service, mock_db):
        """Test that mastery level is stored in session."""
        chat_service.rag_service.get_student_mastery_level.return_value = "A"

        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.mastery_level == "A"

    @pytest.mark.asyncio
    async def test_create_session_different_types(self, chat_service, mock_db):
        """Test creating sessions with different session types."""
        session_types = ["reading_help", "post_paragraph", "test_help", "general_tutor"]

        for st in session_types:
            mock_db.add.reset_mock()
            await chat_service.create_session(
                student_id=10,
                school_id=5,
                session_type=st
            )

            added_session = mock_db.add.call_args[0][0]
            assert added_session.session_type == st


class TestListSessions:
    """Tests for ChatService.list_sessions method."""

    @pytest.mark.asyncio
    async def test_list_sessions_success(self, chat_service, mock_db, sample_chat_session):
        """Test listing sessions with results."""
        # Mock the execute for count query
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        # Mock the execute for main query
        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = [sample_chat_session]

        mock_db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        sessions, total = await chat_service.list_sessions(
            student_id=10,
            school_id=5
        )

        assert total == 1
        assert len(sessions) == 1
        assert sessions[0] == sample_chat_session

    @pytest.mark.asyncio
    async def test_list_sessions_empty(self, chat_service, mock_db):
        """Test listing sessions when no sessions exist."""
        count_result = MagicMock()
        count_result.scalar.return_value = 0

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        sessions, total = await chat_service.list_sessions(
            student_id=10,
            school_id=5
        )

        assert total == 0
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_list_sessions_with_type_filter(self, chat_service, mock_db, sample_chat_session):
        """Test listing sessions filtered by session type."""
        count_result = MagicMock()
        count_result.scalar.return_value = 1

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = [sample_chat_session]

        mock_db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        sessions, total = await chat_service.list_sessions(
            student_id=10,
            school_id=5,
            session_type="general_tutor"
        )

        assert total == 1
        # Query should have filter for session_type

    @pytest.mark.asyncio
    async def test_list_sessions_pagination(self, chat_service, mock_db, sample_chat_session):
        """Test listing sessions with pagination."""
        count_result = MagicMock()
        count_result.scalar.return_value = 50

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = [sample_chat_session]

        mock_db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        sessions, total = await chat_service.list_sessions(
            student_id=10,
            school_id=5,
            page=2,
            page_size=10
        )

        assert total == 50
        # Query should have offset=10 and limit=10

    @pytest.mark.asyncio
    async def test_list_sessions_different_page_sizes(self, chat_service, mock_db):
        """Test listing sessions with different page sizes."""
        count_result = MagicMock()
        count_result.scalar.return_value = 100

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        for page_size in [5, 10, 20, 50]:
            sessions, total = await chat_service.list_sessions(
                student_id=10,
                school_id=5,
                page_size=page_size
            )
            assert total == 100


class TestGetSessionWithMessages:
    """Tests for ChatService.get_session_with_messages method."""

    @pytest.mark.asyncio
    async def test_get_session_success(self, chat_service, mock_db, sample_chat_session):
        """Test getting a session with messages."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=result)

        session = await chat_service.get_session_with_messages(
            session_id=1,
            student_id=10,
            school_id=5
        )

        assert session == sample_chat_session

    @pytest.mark.asyncio
    async def test_get_session_not_found(self, chat_service, mock_db):
        """Test getting a non-existent session."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        session = await chat_service.get_session_with_messages(
            session_id=999,
            student_id=10,
            school_id=5
        )

        assert session is None

    @pytest.mark.asyncio
    async def test_get_session_wrong_student(self, chat_service, mock_db):
        """Test getting session with wrong student ID returns None."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        session = await chat_service.get_session_with_messages(
            session_id=1,
            student_id=999,  # Wrong student
            school_id=5
        )

        assert session is None

    @pytest.mark.asyncio
    async def test_get_session_wrong_school(self, chat_service, mock_db):
        """Test getting session with wrong school ID returns None."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        session = await chat_service.get_session_with_messages(
            session_id=1,
            student_id=10,
            school_id=999  # Wrong school
        )

        assert session is None


class TestDeleteSession:
    """Tests for ChatService.delete_session method."""

    @pytest.mark.asyncio
    async def test_delete_session_success(self, chat_service, mock_db, sample_chat_session):
        """Test successful session deletion (soft delete)."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=result)

        success = await chat_service.delete_session(
            session_id=1,
            student_id=10,
            school_id=5
        )

        assert success is True
        assert sample_chat_session.is_deleted is True
        assert sample_chat_session.deleted_at is not None
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_session_not_found(self, chat_service, mock_db):
        """Test deleting non-existent session."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        success = await chat_service.delete_session(
            session_id=999,
            student_id=10,
            school_id=5
        )

        assert success is False
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_delete_session_wrong_student(self, chat_service, mock_db):
        """Test deleting session with wrong student ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        success = await chat_service.delete_session(
            session_id=1,
            student_id=999,  # Wrong student
            school_id=5
        )

        assert success is False


# =============================================================================
# Message Handling Tests
# =============================================================================

class TestSendMessage:
    """Tests for ChatService.send_message method."""

    @pytest.mark.asyncio
    async def test_send_message_success(self, chat_service, mock_db, sample_chat_session):
        """Test successful message sending."""
        # Setup mocks
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)

        # Mock _get_system_prompt
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="Hello, can you help me?"
        )

        assert response.user_message is not None
        assert response.assistant_message is not None
        assert response.session is not None

        # Verify both messages were added
        assert mock_db.add.call_count == 2
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_session_not_found(self, chat_service, mock_db):
        """Test sending message to non-existent session."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        with pytest.raises(ValueError, match="Chat session .* not found"):
            await chat_service.send_message(
                session_id=999,
                student_id=10,
                school_id=5,
                content="Hello"
            )

    @pytest.mark.asyncio
    async def test_send_message_with_rag_context(self, chat_service, mock_db, sample_chat_session):
        """Test message includes RAG context when available."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)

        # Setup RAG context
        chat_service.rag_service.retrieve_context.return_value = RetrievedContext(
            chunks=[
                {
                    "paragraph_id": 100,
                    "paragraph_title": "Test Paragraph",
                    "chapter_title": "Test Chapter",
                    "chunk_text": "Relevant content here",
                    "similarity": 0.85
                }
            ],
            total_chars=20,
            paragraph_ids={100}
        )
        chat_service.rag_service._build_context_string.return_value = "Context string"
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="What is this about?"
        )

        # Verify RAG was called
        chat_service.rag_service.retrieve_context.assert_called_once()

    @pytest.mark.asyncio
    async def test_send_message_llm_error_handled(self, chat_service, mock_db, sample_chat_session):
        """Test LLM errors are handled gracefully."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)

        # Make LLM raise an error
        chat_service.llm.generate = AsyncMock(side_effect=Exception("LLM failed"))
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="Hello"
        )

        # Should still return a response with error message
        assert "ошибка" in response.assistant_message.content.lower()
        assert response.assistant_message.model_used == "error"

    @pytest.mark.asyncio
    async def test_send_message_updates_session_stats(self, chat_service, mock_db, sample_chat_session):
        """Test that session stats are updated after sending message."""
        sample_chat_session.message_count = 0
        sample_chat_session.total_tokens_used = 0

        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="Hello"
        )

        # message_count should increase by 2 (user + assistant)
        assert sample_chat_session.message_count == 2
        # tokens_used should be updated
        assert sample_chat_session.total_tokens_used == 100  # From mock LLM response
        assert sample_chat_session.last_message_at is not None

    @pytest.mark.asyncio
    async def test_send_message_with_citations(self, chat_service, mock_db, sample_chat_session):
        """Test message response includes citations when context is found."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)

        citations = [
            Citation(
                paragraph_id=100,
                paragraph_title="Test",
                chapter_title="Chapter",
                chunk_text="Content",
                relevance_score=0.85
            )
        ]
        chat_service.rag_service.retrieve_context.return_value = RetrievedContext(
            chunks=[{"paragraph_id": 100, "chunk_text": "test", "similarity": 0.85}],
            total_chars=4,
            paragraph_ids={100}
        )
        chat_service.rag_service._extract_citations.return_value = citations
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="Hello"
        )

        assert response.assistant_message.citations == citations


class TestBuildLLMMessages:
    """Tests for ChatService._build_llm_messages method."""

    @pytest.mark.asyncio
    async def test_build_llm_messages_basic(self, chat_service, sample_chat_session):
        """Test building LLM messages with no history."""
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt text")

        messages = await chat_service._build_llm_messages(
            session=sample_chat_session,
            current_message="User question"
        )

        assert len(messages) == 2  # system + user
        assert messages[0]["role"] == "system"
        assert messages[0]["content"] == "System prompt text"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "User question"

    @pytest.mark.asyncio
    async def test_build_llm_messages_with_history(self, chat_service, sample_chat_session):
        """Test building LLM messages includes conversation history."""
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        # Add some message history
        msg1 = MagicMock()
        msg1.role = "user"
        msg1.content = "Previous question"
        msg1.is_deleted = False

        msg2 = MagicMock()
        msg2.role = "assistant"
        msg2.content = "Previous answer"
        msg2.is_deleted = False

        sample_chat_session.messages = [msg1, msg2]

        messages = await chat_service._build_llm_messages(
            session=sample_chat_session,
            current_message="New question"
        )

        assert len(messages) == 4  # system + 2 history + current user
        assert messages[0]["role"] == "system"
        assert messages[1]["role"] == "user"
        assert messages[1]["content"] == "Previous question"
        assert messages[2]["role"] == "assistant"
        assert messages[3]["role"] == "user"
        assert messages[3]["content"] == "New question"

    @pytest.mark.asyncio
    async def test_build_llm_messages_truncates_history(self, chat_service, sample_chat_session):
        """Test that message history is truncated to MAX_HISTORY_MESSAGES."""
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        # Add more than MAX_HISTORY_MESSAGES
        history = []
        for i in range(15):
            msg = MagicMock()
            msg.role = "user" if i % 2 == 0 else "assistant"
            msg.content = f"Message {i}"
            msg.is_deleted = False
            history.append(msg)

        sample_chat_session.messages = history

        messages = await chat_service._build_llm_messages(
            session=sample_chat_session,
            current_message="New question"
        )

        # Should have system + MAX_HISTORY_MESSAGES + current = 1 + 10 + 1 = 12
        assert len(messages) == 12

    @pytest.mark.asyncio
    async def test_build_llm_messages_excludes_deleted(self, chat_service, sample_chat_session):
        """Test that deleted messages are excluded from history."""
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        msg1 = MagicMock()
        msg1.role = "user"
        msg1.content = "Keep this"
        msg1.is_deleted = False

        msg2 = MagicMock()
        msg2.role = "assistant"
        msg2.content = "Deleted message"
        msg2.is_deleted = True

        sample_chat_session.messages = [msg1, msg2]

        messages = await chat_service._build_llm_messages(
            session=sample_chat_session,
            current_message="New question"
        )

        # Only non-deleted messages should be included
        assert len(messages) == 3  # system + 1 history + current


class TestGetSystemPrompt:
    """Tests for ChatService._get_system_prompt method."""

    @pytest.mark.asyncio
    async def test_get_system_prompt_from_db(self, chat_service, mock_db, sample_system_prompt):
        """Test getting system prompt from database."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_system_prompt
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service._get_system_prompt(
            prompt_type="general_tutor",
            mastery_level="B",
            language="ru"
        )

        assert prompt == sample_system_prompt.prompt_text

    @pytest.mark.asyncio
    async def test_get_system_prompt_fallback_to_default(self, chat_service, mock_db):
        """Test falling back to default prompt when not in DB."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service._get_system_prompt(
            prompt_type="general_tutor",
            mastery_level="B",
            language="ru"
        )

        # Should return default prompt
        assert prompt == DEFAULT_PROMPTS[("general_tutor", "B", "ru")]

    @pytest.mark.asyncio
    async def test_get_system_prompt_level_a(self, chat_service, mock_db):
        """Test getting system prompt for level A."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service._get_system_prompt(
            prompt_type="reading_help",
            mastery_level="A",
            language="ru"
        )

        assert "продвинутый" in prompt.lower()

    @pytest.mark.asyncio
    async def test_get_system_prompt_level_c(self, chat_service, mock_db):
        """Test getting system prompt for level C."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service._get_system_prompt(
            prompt_type="reading_help",
            mastery_level="C",
            language="ru"
        )

        assert "терпеливый" in prompt.lower() or "поддержка" in prompt.lower()

    @pytest.mark.asyncio
    async def test_get_system_prompt_unknown_type_falls_back(self, chat_service, mock_db):
        """Test unknown prompt type falls back to general default."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service._get_system_prompt(
            prompt_type="unknown_type",
            mastery_level="X",
            language="xx"
        )

        # Should fall back to general default
        assert "репетитор" in prompt.lower()


class TestGenerateSessionTitle:
    """Tests for ChatService._generate_session_title method."""

    def test_generate_title_reading_help(self, chat_service):
        """Test title generation for reading_help session."""
        title = chat_service._generate_session_title("reading_help")
        assert "Помощь с чтением" in title

    def test_generate_title_post_paragraph(self, chat_service):
        """Test title generation for post_paragraph session."""
        title = chat_service._generate_session_title("post_paragraph")
        assert "Обсуждение материала" in title

    def test_generate_title_test_help(self, chat_service):
        """Test title generation for test_help session."""
        title = chat_service._generate_session_title("test_help")
        assert "Помощь с тестом" in title

    def test_generate_title_general_tutor(self, chat_service):
        """Test title generation for general_tutor session."""
        title = chat_service._generate_session_title("general_tutor")
        assert "Общие вопросы" in title

    def test_generate_title_unknown_type(self, chat_service):
        """Test title generation for unknown session type."""
        title = chat_service._generate_session_title("unknown_type")
        assert "Чат" in title

    def test_generate_title_includes_datetime(self, chat_service):
        """Test generated title includes date/time."""
        title = chat_service._generate_session_title("general_tutor")
        # Should contain date in format DD.MM.YYYY
        assert "." in title
        assert ":" in title


class TestMessageToResponse:
    """Tests for ChatService._message_to_response method."""

    def test_message_to_response_user_message(self, chat_service, sample_chat_message):
        """Test converting user message to response."""
        response = chat_service._message_to_response(sample_chat_message)

        assert response.id == sample_chat_message.id
        assert response.role == "user"
        assert response.content == sample_chat_message.content
        assert response.citations is None

    def test_message_to_response_with_citations(self, chat_service, sample_chat_message):
        """Test converting message with citations."""
        citations = [
            Citation(
                paragraph_id=100,
                paragraph_title="Test",
                chunk_text="Content",
                relevance_score=0.85
            )
        ]

        response = chat_service._message_to_response(sample_chat_message, citations)

        assert response.citations == citations

    def test_message_to_response_assistant_message(self, chat_service):
        """Test converting assistant message to response."""
        message = MagicMock(spec=ChatMessage)
        message.id = 2
        message.role = "assistant"
        message.content = "AI response"
        message.tokens_used = 100
        message.model_used = "test-model"
        message.processing_time_ms = 500
        message.created_at = datetime.utcnow()

        response = chat_service._message_to_response(message)

        assert response.role == "assistant"
        assert response.tokens_used == 100
        assert response.model_used == "test-model"
        assert response.processing_time_ms == 500


class TestSessionToResponse:
    """Tests for ChatService._session_to_response method."""

    def test_session_to_response_basic(self, chat_service, sample_chat_session):
        """Test converting session to response."""
        response = chat_service._session_to_response(sample_chat_session)

        assert response.id == sample_chat_session.id
        assert response.session_type == sample_chat_session.session_type
        assert response.title == sample_chat_session.title
        assert response.mastery_level == sample_chat_session.mastery_level
        assert response.language == sample_chat_session.language

    def test_session_to_response_with_context_ids(self, chat_service, sample_chat_session):
        """Test converting session with context IDs."""
        sample_chat_session.paragraph_id = 100
        sample_chat_session.chapter_id = 50
        sample_chat_session.test_id = 25

        response = chat_service._session_to_response(sample_chat_session)

        assert response.paragraph_id == 100
        assert response.chapter_id == 50
        assert response.test_id == 25


# =============================================================================
# System Prompt Management Tests
# =============================================================================

class TestListPrompts:
    """Tests for ChatService.list_prompts method."""

    @pytest.mark.asyncio
    async def test_list_prompts_all(self, chat_service, mock_db, sample_system_prompt):
        """Test listing all prompts."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_system_prompt]
        mock_db.execute = AsyncMock(return_value=result)

        prompts = await chat_service.list_prompts()

        assert len(prompts) == 1
        assert prompts[0] == sample_system_prompt

    @pytest.mark.asyncio
    async def test_list_prompts_filter_by_type(self, chat_service, mock_db, sample_system_prompt):
        """Test listing prompts filtered by type."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_system_prompt]
        mock_db.execute = AsyncMock(return_value=result)

        prompts = await chat_service.list_prompts(prompt_type="general_tutor")

        assert len(prompts) == 1

    @pytest.mark.asyncio
    async def test_list_prompts_filter_by_mastery_level(self, chat_service, mock_db, sample_system_prompt):
        """Test listing prompts filtered by mastery level."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_system_prompt]
        mock_db.execute = AsyncMock(return_value=result)

        prompts = await chat_service.list_prompts(mastery_level="B")

        assert len(prompts) == 1

    @pytest.mark.asyncio
    async def test_list_prompts_filter_by_language(self, chat_service, mock_db, sample_system_prompt):
        """Test listing prompts filtered by language."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_system_prompt]
        mock_db.execute = AsyncMock(return_value=result)

        prompts = await chat_service.list_prompts(language="ru")

        assert len(prompts) == 1

    @pytest.mark.asyncio
    async def test_list_prompts_include_inactive(self, chat_service, mock_db, sample_system_prompt):
        """Test listing prompts including inactive ones."""
        sample_system_prompt.is_active = False
        result = MagicMock()
        result.scalars.return_value.all.return_value = [sample_system_prompt]
        mock_db.execute = AsyncMock(return_value=result)

        prompts = await chat_service.list_prompts(include_inactive=True)

        assert len(prompts) == 1

    @pytest.mark.asyncio
    async def test_list_prompts_empty(self, chat_service, mock_db):
        """Test listing prompts when none exist."""
        result = MagicMock()
        result.scalars.return_value.all.return_value = []
        mock_db.execute = AsyncMock(return_value=result)

        prompts = await chat_service.list_prompts()

        assert len(prompts) == 0


class TestGetPromptById:
    """Tests for ChatService.get_prompt_by_id method."""

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_success(self, chat_service, mock_db, sample_system_prompt):
        """Test getting prompt by ID."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_system_prompt
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service.get_prompt_by_id(1)

        assert prompt == sample_system_prompt

    @pytest.mark.asyncio
    async def test_get_prompt_by_id_not_found(self, chat_service, mock_db):
        """Test getting non-existent prompt."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        prompt = await chat_service.get_prompt_by_id(999)

        assert prompt is None


class TestCreatePrompt:
    """Tests for ChatService.create_prompt method."""

    @pytest.mark.asyncio
    async def test_create_prompt_success(self, chat_service, mock_db):
        """Test successful prompt creation."""
        data = SystemPromptCreate(
            prompt_type="general_tutor",
            mastery_level="B",
            language="ru",
            name="Test Prompt",
            prompt_text="This is a test prompt text"
        )

        await chat_service.create_prompt(data)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_prompt_with_all_fields(self, chat_service, mock_db):
        """Test creating prompt with all fields."""
        data = SystemPromptCreate(
            prompt_type="reading_help",
            mastery_level="A",
            language="kk",
            name="Advanced Reader",
            description="For advanced readers",
            prompt_text="You are an advanced tutor...",
            is_active=True
        )

        await chat_service.create_prompt(data)

        added_prompt = mock_db.add.call_args[0][0]
        assert added_prompt.prompt_type == "reading_help"
        assert added_prompt.mastery_level == "A"
        assert added_prompt.language == "kk"


class TestUpdatePrompt:
    """Tests for ChatService.update_prompt method."""

    @pytest.mark.asyncio
    async def test_update_prompt_success(self, chat_service, mock_db, sample_system_prompt):
        """Test successful prompt update."""
        # Mock get_prompt_by_id
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_system_prompt
        mock_db.execute = AsyncMock(return_value=result)

        data = SystemPromptUpdate(
            name="Updated Name",
            prompt_text="Updated prompt text here"
        )

        updated = await chat_service.update_prompt(1, data)

        assert updated.name == "Updated Name"
        assert updated.prompt_text == "Updated prompt text here"
        assert updated.version == 2  # Version incremented
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_prompt_partial(self, chat_service, mock_db, sample_system_prompt):
        """Test partial prompt update."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_system_prompt
        mock_db.execute = AsyncMock(return_value=result)

        original_text = sample_system_prompt.prompt_text
        data = SystemPromptUpdate(name="Only Name Updated")

        updated = await chat_service.update_prompt(1, data)

        assert updated.name == "Only Name Updated"
        # prompt_text should remain unchanged
        assert updated.prompt_text == original_text

    @pytest.mark.asyncio
    async def test_update_prompt_not_found(self, chat_service, mock_db):
        """Test updating non-existent prompt."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        data = SystemPromptUpdate(name="Updated")

        updated = await chat_service.update_prompt(999, data)

        assert updated is None
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_prompt_toggle_active(self, chat_service, mock_db, sample_system_prompt):
        """Test toggling prompt active status."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_system_prompt
        mock_db.execute = AsyncMock(return_value=result)

        data = SystemPromptUpdate(is_active=False)

        updated = await chat_service.update_prompt(1, data)

        assert updated.is_active is False


class TestDeletePrompt:
    """Tests for ChatService.delete_prompt method."""

    @pytest.mark.asyncio
    async def test_delete_prompt_success(self, chat_service, mock_db, sample_system_prompt):
        """Test successful prompt deletion."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = sample_system_prompt
        mock_db.execute = AsyncMock(return_value=result)

        success = await chat_service.delete_prompt(1)

        assert success is True
        mock_db.delete.assert_called_once_with(sample_system_prompt)
        mock_db.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_prompt_not_found(self, chat_service, mock_db):
        """Test deleting non-existent prompt."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        success = await chat_service.delete_prompt(999)

        assert success is False
        mock_db.delete.assert_not_called()


# =============================================================================
# Edge Cases and Error Handling
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    @pytest.mark.asyncio
    async def test_send_message_unicode_content(self, chat_service, mock_db, sample_chat_session):
        """Test sending message with unicode characters."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        unicode_content = "Привет! Как дела? 你好 🎉 مرحبا"

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content=unicode_content
        )

        # Should handle unicode without errors
        assert response.user_message is not None

    @pytest.mark.asyncio
    async def test_send_message_very_long_content(self, chat_service, mock_db, sample_chat_session):
        """Test sending message with very long content."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        long_content = "A" * 3000  # 3000 characters

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content=long_content
        )

        assert response.user_message is not None

    @pytest.mark.asyncio
    async def test_send_message_empty_conversation(self, chat_service, mock_db, sample_chat_session):
        """Test sending first message in a session."""
        sample_chat_session.messages = []
        sample_chat_session.message_count = 0

        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="First message"
        )

        assert response.user_message is not None
        assert sample_chat_session.message_count == 2

    @pytest.mark.asyncio
    async def test_list_sessions_count_is_none(self, chat_service, mock_db):
        """Test list_sessions when count returns None."""
        count_result = MagicMock()
        count_result.scalar.return_value = None  # Can happen with empty DB

        sessions_result = MagicMock()
        sessions_result.scalars.return_value.all.return_value = []

        mock_db.execute = AsyncMock(side_effect=[count_result, sessions_result])

        sessions, total = await chat_service.list_sessions(
            student_id=10,
            school_id=5
        )

        assert total == 0  # Should default to 0, not None
        assert len(sessions) == 0

    @pytest.mark.asyncio
    async def test_create_session_with_all_optional_ids(self, chat_service, mock_db):
        """Test creating session with all optional context IDs."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="reading_help",
            paragraph_id=100,
            chapter_id=50,
            test_id=25,
            title="Full Context Session",
            language="kk"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.paragraph_id == 100
        assert added_session.chapter_id == 50
        assert added_session.test_id == 25
        assert added_session.language == "kk"

    @pytest.mark.asyncio
    async def test_send_message_with_empty_rag_context(self, chat_service, mock_db, sample_chat_session):
        """Test sending message when RAG returns no context."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)

        chat_service.rag_service.retrieve_context.return_value = RetrievedContext(
            chunks=[],
            total_chars=0,
            paragraph_ids=set()
        )
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="Hello"
        )

        # Should still work without RAG context
        assert response.user_message is not None
        assert response.assistant_message is not None

    def test_default_prompts_exist_for_all_levels(self):
        """Test that DEFAULT_PROMPTS has entries for all mastery levels."""
        for level in ["A", "B", "C"]:
            for prompt_type in ["reading_help", "general_tutor"]:
                key = (prompt_type, level, "ru")
                assert key in DEFAULT_PROMPTS, f"Missing default prompt for {key}"

    def test_max_history_messages_constant(self, chat_service):
        """Test MAX_HISTORY_MESSAGES constant is set."""
        assert chat_service.MAX_HISTORY_MESSAGES == 10

    @pytest.mark.asyncio
    async def test_send_message_processing_time_calculated(self, chat_service, mock_db, sample_chat_session):
        """Test that processing time is calculated for response."""
        get_session_result = MagicMock()
        get_session_result.scalar_one_or_none.return_value = sample_chat_session
        mock_db.execute = AsyncMock(return_value=get_session_result)
        chat_service._get_system_prompt = AsyncMock(return_value="System prompt")

        response = await chat_service.send_message(
            session_id=1,
            student_id=10,
            school_id=5,
            content="Hello"
        )

        # Verify assistant message was created with processing_time_ms
        added_messages = [call[0][0] for call in mock_db.add.call_args_list]
        assistant_msg = [m for m in added_messages if hasattr(m, 'role') and m.role == 'assistant']
        if assistant_msg:
            assert assistant_msg[0].processing_time_ms is not None
            assert assistant_msg[0].processing_time_ms >= 0


class TestMultipleMasteryLevels:
    """Tests for different mastery levels behavior."""

    @pytest.mark.asyncio
    async def test_session_created_with_level_a(self, chat_service, mock_db):
        """Test session creation with level A mastery."""
        chat_service.rag_service.get_student_mastery_level.return_value = "A"

        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.mastery_level == "A"

    @pytest.mark.asyncio
    async def test_session_created_with_level_c(self, chat_service, mock_db):
        """Test session creation with level C mastery."""
        chat_service.rag_service.get_student_mastery_level.return_value = "C"

        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.mastery_level == "C"

    @pytest.mark.asyncio
    async def test_system_prompt_varies_by_mastery_level(self, chat_service, mock_db):
        """Test that system prompts differ by mastery level."""
        result = MagicMock()
        result.scalar_one_or_none.return_value = None
        mock_db.execute = AsyncMock(return_value=result)

        prompt_a = await chat_service._get_system_prompt("reading_help", "A", "ru")
        prompt_b = await chat_service._get_system_prompt("reading_help", "B", "ru")
        prompt_c = await chat_service._get_system_prompt("reading_help", "C", "ru")

        # All should be different
        assert prompt_a != prompt_b
        assert prompt_b != prompt_c
        assert prompt_a != prompt_c


class TestLanguageSupport:
    """Tests for multi-language support."""

    @pytest.mark.asyncio
    async def test_create_session_russian(self, chat_service, mock_db):
        """Test creating session with Russian language."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor",
            language="ru"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.language == "ru"

    @pytest.mark.asyncio
    async def test_create_session_kazakh(self, chat_service, mock_db):
        """Test creating session with Kazakh language."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor",
            language="kk"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.language == "kk"

    @pytest.mark.asyncio
    async def test_default_language_is_russian(self, chat_service, mock_db):
        """Test default language is Russian."""
        await chat_service.create_session(
            student_id=10,
            school_id=5,
            session_type="general_tutor"
        )

        added_session = mock_db.add.call_args[0][0]
        assert added_session.language == "ru"
