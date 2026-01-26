"""
Chat Service for RAG-based conversations.

Integrates with:
- RAGService for context retrieval
- LLMService for response generation
- MasteryRepository for A/B/C personalization
"""
import json
import logging
import time
from typing import Optional, List, Tuple, AsyncIterator, Any, Dict
from datetime import datetime
from zoneinfo import ZoneInfo

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage
from app.models.system_prompt import SystemPromptTemplate
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService, LLMResponse, LLMStreamChunk
from app.schemas.chat import (
    ChatSessionResponse,
    ChatMessageResponse,
    ChatResponse,
    SystemPromptCreate,
    SystemPromptUpdate,
)
from app.schemas.rag import Citation

logger = logging.getLogger(__name__)


# Default prompts (fallback if no DB entry)
DEFAULT_PROMPTS = {
    ("reading_help", "A", "ru"): """Ты — продвинутый репетитор, помогающий сильному ученику с чтением материала.
Ученик уровня A (85%+ баллов). Будь кратким, используй сложную терминологию.
Язык: русский. Цитируй источники.""",

    ("reading_help", "B", "ru"): """Ты — репетитор, помогающий ученику среднего уровня понять материал.
Ученик уровня B (60-84% баллов). Давай чёткие объяснения с примерами.
Язык: русский. Цитируй источники.""",

    ("reading_help", "C", "ru"): """Ты — терпеливый репетитор, помогающий ученику, которому нужна дополнительная поддержка.
Ученик уровня C (ниже 60%). Используй простой язык и много примеров.
Язык: русский. Цитируй источники.""",

    ("general_tutor", "A", "ru"): """Ты — репетитор для продвинутого ученика (уровень A).
Отвечай кратко, глубоко, с использованием сложных концепций.
Язык: русский.""",

    ("general_tutor", "B", "ru"): """Ты — репетитор для ученика среднего уровня (уровень B).
Давай чёткие объяснения с примерами.
Язык: русский.""",

    ("general_tutor", "C", "ru"): """Ты — терпеливый репетитор для ученика (уровень C).
Используй простой язык и много примеров.
Язык: русский.""",
}


class ChatService:
    """Service for managing chat sessions and messages."""

    # Maximum messages to include in LLM context
    MAX_HISTORY_MESSAGES = 10

    def __init__(self, db: AsyncSession):
        self.db = db
        self.rag_service = RAGService(db)
        self.llm = LLMService()

    # =========================================================================
    # Session Management
    # =========================================================================

    async def create_session(
        self,
        student_id: int,
        school_id: int,
        session_type: str,
        paragraph_id: Optional[int] = None,
        chapter_id: Optional[int] = None,
        test_id: Optional[int] = None,
        title: Optional[str] = None,
        language: str = "ru"
    ) -> ChatSession:
        """Create a new chat session."""

        # Get student's mastery level
        mastery_level = await self.rag_service.get_student_mastery_level(
            student_id=student_id,
            school_id=school_id,
            chapter_id=chapter_id
        )

        # Auto-generate title if not provided
        if not title:
            title = self._generate_session_title(session_type)

        session = ChatSession(
            student_id=student_id,
            school_id=school_id,
            session_type=session_type,  # Store as string
            paragraph_id=paragraph_id,
            chapter_id=chapter_id,
            test_id=test_id,
            title=title,
            mastery_level=mastery_level,
            language=language
        )

        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)

        logger.info(
            f"Created chat session {session.id} for student {student_id}, "
            f"type={session_type}, level={mastery_level}"
        )

        return session

    async def list_sessions(
        self,
        student_id: int,
        school_id: int,
        session_type: Optional[str] = None,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[ChatSession], int]:
        """List student's chat sessions with pagination."""

        query = select(ChatSession).where(
            ChatSession.student_id == student_id,
            ChatSession.school_id == school_id,
            ChatSession.is_deleted == False
        )

        if session_type:
            query = query.where(ChatSession.session_type == session_type)

        # Count total
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Apply pagination
        query = query.order_by(
            ChatSession.last_message_at.desc().nullslast(),
            ChatSession.created_at.desc()
        )
        query = query.offset((page - 1) * page_size).limit(page_size)

        result = await self.db.execute(query)
        sessions = list(result.scalars().all())

        return sessions, total

    async def get_session_with_messages(
        self,
        session_id: int,
        student_id: int,
        school_id: int
    ) -> Optional[ChatSession]:
        """Get session with all messages loaded."""

        query = (
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.id == session_id,
                ChatSession.student_id == student_id,
                ChatSession.school_id == school_id,
                ChatSession.is_deleted == False
            )
        )

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def delete_session(
        self,
        session_id: int,
        student_id: int,
        school_id: int
    ) -> bool:
        """Soft delete a chat session."""

        query = select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.student_id == student_id,
            ChatSession.school_id == school_id,
            ChatSession.is_deleted == False
        )

        result = await self.db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            return False

        session.is_deleted = True
        session.deleted_at = datetime.utcnow()

        await self.db.commit()
        return True

    # =========================================================================
    # Message Handling
    # =========================================================================

    async def send_message(
        self,
        session_id: int,
        student_id: int,
        school_id: int,
        content: str
    ) -> ChatResponse:
        """Send a user message and generate AI response."""

        start_time = time.time()

        # Get session with messages
        session = await self.get_session_with_messages(session_id, student_id, school_id)
        if not session:
            raise ValueError(f"Chat session {session_id} not found")

        # 1. Save user message
        user_message = ChatMessage(
            session_id=session_id,
            school_id=school_id,
            role="user",
            content=content
        )
        self.db.add(user_message)
        await self.db.flush()  # Get ID

        # 2. Build conversation history for LLM
        messages = await self._build_llm_messages(session, content)

        # 3. Retrieve relevant context via RAG
        context = await self.rag_service.retrieve_context(
            query=content,
            chapter_id=session.chapter_id,
            paragraph_ids=[session.paragraph_id] if session.paragraph_id else None
        )

        # 4. Add context to the last user message if found
        if context.chunks:
            context_string = self.rag_service._build_context_string(context.chunks)
            messages[-1]["content"] = f"""Контекст из учебника:
---
{context_string}
---

Вопрос ученика: {content}"""

        # 5. Generate AI response
        try:
            llm_response: LLMResponse = await self.llm.generate(
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            )
        except Exception as e:
            logger.error(f"LLM generation failed: {str(e)}")
            llm_response = LLMResponse(
                content="Извините, произошла ошибка при генерации ответа. Попробуйте позже.",
                model="error",
                tokens_used=0
            )

        processing_time = int((time.time() - start_time) * 1000)

        # 6. Extract citations
        citations = self.rag_service._extract_citations(context.chunks) if context.chunks else []

        # 7. Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            school_id=school_id,
            role="assistant",
            content=llm_response.content,
            citations_json=json.dumps([c.model_dump() for c in citations]) if citations else None,
            context_chunks_used=len(context.chunks) if context.chunks else 0,
            tokens_used=llm_response.tokens_used,
            model_used=llm_response.model,
            processing_time_ms=processing_time
        )
        self.db.add(assistant_message)

        # 8. Update session stats
        session.message_count += 2
        session.total_tokens_used += (llm_response.tokens_used or 0)
        session.last_message_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user_message)
        await self.db.refresh(assistant_message)
        await self.db.refresh(session)

        logger.info(
            f"Chat response: session={session_id}, tokens={llm_response.tokens_used}, "
            f"chunks={len(context.chunks) if context.chunks else 0}, time={processing_time}ms"
        )

        return ChatResponse(
            user_message=self._message_to_response(user_message),
            assistant_message=self._message_to_response(assistant_message, citations),
            session=self._session_to_response(session)
        )

    async def send_message_stream(
        self,
        session_id: int,
        student_id: int,
        school_id: int,
        content: str
    ) -> AsyncIterator[Dict[str, Any]]:
        """
        Send a user message and stream AI response.

        Yields SSE events:
        - {"type": "user_message", "message": {...}}
        - {"type": "delta", "content": "..."}
        - {"type": "done", "message": {...}, "session": {...}, "citations": [...]}
        - {"type": "error", "error": "..."}
        """
        start_time = time.time()

        # Get session with messages
        session = await self.get_session_with_messages(session_id, student_id, school_id)
        if not session:
            yield {"type": "error", "error": f"Chat session {session_id} not found"}
            return

        # 1. Save user message
        user_message = ChatMessage(
            session_id=session_id,
            school_id=school_id,
            role="user",
            content=content
        )
        self.db.add(user_message)
        await self.db.flush()

        # Yield user message immediately
        yield {
            "type": "user_message",
            "message": self._message_to_response(user_message).model_dump(mode="json")
        }

        # 2. Build conversation history for LLM
        messages = await self._build_llm_messages(session, content)

        # 3. Retrieve relevant context via RAG
        context = await self.rag_service.retrieve_context(
            query=content,
            chapter_id=session.chapter_id,
            paragraph_ids=[session.paragraph_id] if session.paragraph_id else None
        )

        # 4. Add context to the last user message if found
        if context.chunks:
            context_string = self.rag_service._build_context_string(context.chunks)
            messages[-1]["content"] = f"""Контекст из учебника:
---
{context_string}
---

Вопрос ученика: {content}"""

        # 5. Stream AI response
        full_content = ""
        tokens_used = 0
        finish_reason = None

        try:
            async for chunk in self.llm.stream_generate(
                messages=messages,
                temperature=0.7,
                max_tokens=1500
            ):
                if chunk.content:
                    full_content += chunk.content
                    yield {"type": "delta", "content": chunk.content}

                if chunk.is_final:
                    tokens_used = chunk.tokens_used or 0
                    finish_reason = chunk.finish_reason

        except Exception as e:
            logger.error(f"LLM streaming failed: {str(e)}")
            full_content = "Извините, произошла ошибка при генерации ответа. Попробуйте позже."
            yield {"type": "delta", "content": full_content}

        processing_time = int((time.time() - start_time) * 1000)

        # 6. Extract citations
        citations = self.rag_service._extract_citations(context.chunks) if context.chunks else []

        # 7. Save assistant message
        assistant_message = ChatMessage(
            session_id=session_id,
            school_id=school_id,
            role="assistant",
            content=full_content,
            citations_json=json.dumps([c.model_dump() for c in citations]) if citations else None,
            context_chunks_used=len(context.chunks) if context.chunks else 0,
            tokens_used=tokens_used,
            model_used=self.llm.provider,
            processing_time_ms=processing_time
        )
        self.db.add(assistant_message)

        # 8. Update session stats
        session.message_count += 2
        session.total_tokens_used += tokens_used
        session.last_message_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(user_message)
        await self.db.refresh(assistant_message)
        await self.db.refresh(session)

        logger.info(
            f"Chat stream response: session={session_id}, tokens={tokens_used}, "
            f"chunks={len(context.chunks) if context.chunks else 0}, time={processing_time}ms"
        )

        # Yield final message with metadata
        yield {
            "type": "done",
            "message": self._message_to_response(assistant_message, citations).model_dump(mode="json"),
            "session": self._session_to_response(session).model_dump(mode="json"),
            "citations": [c.model_dump(mode="json") for c in citations]
        }

    async def _build_llm_messages(
        self,
        session: ChatSession,
        current_message: str
    ) -> List[dict]:
        """Build LLM messages array from conversation history."""

        # 1. Get system prompt
        system_prompt = await self._get_system_prompt(
            prompt_type=session.session_type,  # Already a string
            mastery_level=session.mastery_level or "B",
            language=session.language
        )

        messages = [{"role": "system", "content": system_prompt}]

        # 2. Add conversation history (last N messages)
        history_messages = [
            m for m in session.messages
            if not m.is_deleted
        ][-self.MAX_HISTORY_MESSAGES:]

        for msg in history_messages:
            messages.append({
                "role": msg.role,
                "content": msg.content
            })

        # 3. Add current user message
        messages.append({"role": "user", "content": current_message})

        return messages

    async def _get_system_prompt(
        self,
        prompt_type: str,
        mastery_level: str,
        language: str
    ) -> str:
        """Get system prompt from DB or use default."""

        query = select(SystemPromptTemplate).where(
            SystemPromptTemplate.prompt_type == prompt_type,
            SystemPromptTemplate.mastery_level == mastery_level,
            SystemPromptTemplate.language == language,
            SystemPromptTemplate.is_active == True
        )

        result = await self.db.execute(query)
        prompt = result.scalar_one_or_none()

        if prompt:
            return prompt.prompt_text

        # Fallback to default
        key = (prompt_type, mastery_level, language)
        return DEFAULT_PROMPTS.get(
            key,
            DEFAULT_PROMPTS.get(
                ("general_tutor", "B", "ru"),
                "Ты — полезный репетитор. Помогай ученику понять материал."
            )
        )

    def _generate_session_title(self, session_type: str) -> str:
        """Generate default session title."""
        type_names = {
            "reading_help": "Помощь с чтением",
            "post_paragraph": "Обсуждение материала",
            "test_help": "Помощь с тестом",
            "general_tutor": "Общие вопросы"
        }
        # Use Kazakhstan timezone for title
        almaty_time = datetime.now(ZoneInfo('Asia/Almaty'))
        return f"{type_names.get(session_type, 'Чат')} - {almaty_time.strftime('%d.%m.%Y %H:%M')}"

    def _message_to_response(
        self,
        message: ChatMessage,
        citations: Optional[List[Citation]] = None
    ) -> ChatMessageResponse:
        """Convert ChatMessage to response schema."""
        return ChatMessageResponse(
            id=message.id,
            role=message.role,
            content=message.content,
            citations=citations,
            tokens_used=message.tokens_used,
            model_used=message.model_used,
            processing_time_ms=message.processing_time_ms,
            created_at=message.created_at
        )

    def _session_to_response(self, session: ChatSession) -> ChatSessionResponse:
        """Convert ChatSession to response schema."""
        return ChatSessionResponse(
            id=session.id,
            session_type=session.session_type,  # Already a string
            paragraph_id=session.paragraph_id,
            chapter_id=session.chapter_id,
            test_id=session.test_id,
            title=session.title,
            mastery_level=session.mastery_level,
            language=session.language,
            message_count=session.message_count,
            total_tokens_used=session.total_tokens_used,
            last_message_at=session.last_message_at,
            created_at=session.created_at
        )

    # =========================================================================
    # System Prompt Management
    # =========================================================================

    async def list_prompts(
        self,
        prompt_type: Optional[str] = None,
        mastery_level: Optional[str] = None,
        language: Optional[str] = None,
        include_inactive: bool = False
    ) -> List[SystemPromptTemplate]:
        """List system prompt templates."""

        query = select(SystemPromptTemplate)

        if prompt_type:
            query = query.where(SystemPromptTemplate.prompt_type == prompt_type)
        if mastery_level:
            query = query.where(SystemPromptTemplate.mastery_level == mastery_level)
        if language:
            query = query.where(SystemPromptTemplate.language == language)
        if not include_inactive:
            query = query.where(SystemPromptTemplate.is_active == True)

        query = query.order_by(
            SystemPromptTemplate.prompt_type,
            SystemPromptTemplate.mastery_level,
            SystemPromptTemplate.language
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_prompt_by_id(self, prompt_id: int) -> Optional[SystemPromptTemplate]:
        """Get a system prompt by ID."""
        result = await self.db.execute(
            select(SystemPromptTemplate).where(SystemPromptTemplate.id == prompt_id)
        )
        return result.scalar_one_or_none()

    async def create_prompt(self, data: SystemPromptCreate) -> SystemPromptTemplate:
        """Create a new system prompt template."""

        prompt = SystemPromptTemplate(**data.model_dump())
        self.db.add(prompt)
        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def update_prompt(
        self,
        prompt_id: int,
        data: SystemPromptUpdate
    ) -> Optional[SystemPromptTemplate]:
        """Update a system prompt template."""

        prompt = await self.get_prompt_by_id(prompt_id)
        if not prompt:
            return None

        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(prompt, field, value)

        prompt.version += 1  # Increment version

        await self.db.commit()
        await self.db.refresh(prompt)
        return prompt

    async def delete_prompt(self, prompt_id: int) -> bool:
        """Delete a system prompt template."""

        prompt = await self.get_prompt_by_id(prompt_id)
        if not prompt:
            return False

        await self.db.delete(prompt)
        await self.db.commit()
        return True
