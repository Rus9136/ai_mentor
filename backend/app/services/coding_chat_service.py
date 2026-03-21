"""
Coding AI Mentor Service.

Provides AI-assisted help for coding challenges:
- Hints (guiding questions without giving solutions)
- Error explanations (traceback analysis for schoolkids)
- Code reviews (style, efficiency, bugs)
- Step-by-step execution traces

Reuses ChatSession/ChatMessage models and LLMService,
but does NOT use RAG or AI memory (not relevant for coding).
"""
import logging
import time
from datetime import datetime, timedelta
from typing import Optional, List, AsyncIterator, Any, Dict

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.chat import ChatSession, ChatMessage
from app.models.coding import CodingChallenge
from app.models.llm_usage_log import LLMFeature
from app.schemas.chat import ChatSessionResponse, ChatMessageResponse
from app.schemas.coding_chat import CodingAction
from app.services.llm_service import LLMService, LLMResponse, LLMUsageContext

logger = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 10
SESSION_REUSE_HOURS = 24


SYSTEM_PROMPTS = {
    "ru": """Ты — учитель информатики. Помогаешь школьнику 7-11 класса с программированием на Python.

ПРАВИЛА:
1. НИКОГДА не давай готовое решение целиком
2. Используй наводящие вопросы, намёки, аналогии
3. Если ученик совсем застрял — можно показать фрагмент (1-2 строки), но не всё решение
4. Объясняй ошибки простым языком, как для школьника
5. Хвали за правильные подходы, даже если код неидеален
6. Отвечай кратко и по делу — не больше 200 слов

--- ЗАДАЧА ---
Название: {title}
Условие:
{description}
Сложность: {difficulty}""",

    "kk": """Сен — информатика пәнінің мұғалімісің. 7-11 сынып оқушысына Python бағдарламалау тілінде көмектесесің.

ЕРЕЖЕЛЕР:
1. ЕШҚАШАН дайын шешімді толығымен берме
2. Бағыттаушы сұрақтар, кеңестер, ұқсастықтар қолдан
3. Оқушы мүлдем тұрып қалса — фрагмент көрсетуге болады (1-2 жол), бірақ толық шешімді емес
4. Қателерді қарапайым тілмен түсіндір
5. Дұрыс тәсілдерді мақта, код мінсіз болмаса да
6. Қысқа және нақты жауап бер — 200 сөзден аспасын

--- ТАПСЫРМА ---
Атауы: {title}
Шарты:
{description}
Күрделілігі: {difficulty}""",
}


ACTION_PROMPTS = {
    CodingAction.HINT: {
        "ru": "Ученик работает над задачей и просит подсказку.\n\nКод ученика:\n```python\n{code}\n```\n{error_block}\nДай наводящий вопрос или подсказку. Не давай готовое решение.",
        "kk": "Оқушы тапсырма үстінде жұмыс істеп жатыр және кеңес сұрайды.\n\nОқушының коды:\n```python\n{code}\n```\n{error_block}\nБағыттаушы сұрақ немесе кеңес бер. Дайын шешім берме.",
    },
    CodingAction.EXPLAIN_ERROR: {
        "ru": "Ученик получил ошибку и не понимает её.\n\nКод:\n```python\n{code}\n```\n\nОшибка:\n```\n{error}\n```\nОбъясни ошибку простым языком для школьника. Покажи какая строка вызвала проблему и как её исправить.",
        "kk": "Оқушы қате алды және оны түсінбейді.\n\nКод:\n```python\n{code}\n```\n\nҚате:\n```\n{error}\n```\nҚатені қарапайым тілмен түсіндір. Қай жол мәселе тудырғанын және оны қалай түзетуге болатынын көрсет.",
    },
    CodingAction.CODE_REVIEW: {
        "ru": "Ученик просит проверить свой код.\n\nКод:\n```python\n{code}\n```\n{test_block}\nОцени код: стиль, эффективность, возможные баги. Не переписывай код целиком, дай конкретные советы по улучшению.",
        "kk": "Оқушы өз кодын тексеруді сұрайды.\n\nКод:\n```python\n{code}\n```\n{test_block}\nКодты бағала: стиль, тиімділік, ықтимал қателер. Кодты толығымен қайта жазба, нақты жақсарту кеңестерін бер.",
    },
    CodingAction.STEP_BY_STEP: {
        "ru": "Ученик хочет понять как работает его код.\n\nКод:\n```python\n{code}\n```\nПокажи пошаговое выполнение кода с состоянием переменных на каждом шаге.\nФормат:\nШаг 1: `строка кода` → переменные: x=5, y=3\nШаг 2: ...",
        "kk": "Оқушы өз кодының қалай жұмыс істейтінін түсінгісі келеді.\n\nКод:\n```python\n{code}\n```\nКодтың қадамдық орындалуын әр қадамдағы айнымалылар күйімен көрсет.\nФормат:\nҚадам 1: `код жолы` → айнымалылар: x=5, y=3\nҚадам 2: ...",
    },
}


class CodingChatService:
    """AI mentor service for coding challenges."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.llm = LLMService()

    async def _ensure_rls_context(self, school_id: int) -> None:
        """Set RLS tenant context (defensive for streaming)."""
        await self.db.execute(
            text("SELECT set_config('app.current_tenant_id', :tid, false)"),
            {"tid": str(school_id)}
        )

    # =========================================================================
    # Session Management
    # =========================================================================

    async def get_or_create_session(
        self,
        student_id: int,
        school_id: int,
        challenge_id: int,
        language: str = "ru",
    ) -> ChatSession:
        """Find existing coding session for this challenge or create a new one."""
        await self._ensure_rls_context(school_id)

        cutoff = datetime.utcnow() - timedelta(hours=SESSION_REUSE_HOURS)
        result = await self.db.execute(
            select(ChatSession)
            .where(
                ChatSession.student_id == student_id,
                ChatSession.school_id == school_id,
                ChatSession.challenge_id == challenge_id,
                ChatSession.session_type == "coding",
                ChatSession.is_deleted == False,
                ChatSession.created_at > cutoff,
            )
            .order_by(ChatSession.created_at.desc())
            .limit(1)
        )
        session = result.scalar_one_or_none()

        if session:
            return session

        session = ChatSession(
            student_id=student_id,
            school_id=school_id,
            session_type="coding",
            challenge_id=challenge_id,
            language=language,
            title=None,
            message_count=0,
            total_tokens_used=0,
        )
        self.db.add(session)
        await self.db.flush()
        return session

    async def get_session_with_messages(
        self,
        session_id: int,
        student_id: int,
        school_id: int,
    ) -> Optional[ChatSession]:
        """Load a coding chat session with its messages."""
        await self._ensure_rls_context(school_id)

        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.id == session_id,
                ChatSession.student_id == student_id,
                ChatSession.school_id == school_id,
                ChatSession.session_type == "coding",
                ChatSession.is_deleted == False,
            )
        )
        return result.scalar_one_or_none()

    async def get_challenge_session(
        self,
        challenge_id: int,
        student_id: int,
        school_id: int,
    ) -> Optional[ChatSession]:
        """Find the active coding chat session for a specific challenge."""
        await self._ensure_rls_context(school_id)

        cutoff = datetime.utcnow() - timedelta(hours=SESSION_REUSE_HOURS)
        result = await self.db.execute(
            select(ChatSession)
            .options(selectinload(ChatSession.messages))
            .where(
                ChatSession.student_id == student_id,
                ChatSession.school_id == school_id,
                ChatSession.challenge_id == challenge_id,
                ChatSession.session_type == "coding",
                ChatSession.is_deleted == False,
                ChatSession.created_at > cutoff,
            )
            .order_by(ChatSession.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    # =========================================================================
    # AI Actions (Streaming)
    # =========================================================================

    async def start_action_stream(
        self,
        student_id: int,
        school_id: int,
        challenge: CodingChallenge,
        action: CodingAction,
        code: str,
        language: str = "ru",
        error: Optional[str] = None,
        test_results: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Start an AI action and stream the response via SSE events."""
        start_time = time.time()
        await self._ensure_rls_context(school_id)

        # Get or create session
        session = await self.get_or_create_session(
            student_id, school_id, challenge.id, language
        )

        # Format action-specific user message
        user_content = self._format_action_message(action, code, language, error, test_results)

        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            school_id=school_id,
            role="user",
            content=user_content,
        )
        self.db.add(user_message)
        await self.db.flush()

        yield {
            "type": "user_message",
            "message": _message_to_dict(user_message),
        }

        # Build LLM messages
        system_prompt = self._build_system_prompt(challenge, language)
        messages = self._build_llm_messages(session, system_prompt, user_content)

        # Stream LLM response
        full_content = ""
        tokens_used = 0
        generation_error = False

        try:
            async for chunk in self.llm.stream_generate(
                messages=messages,
                temperature=0.7,
                max_tokens=1500,
            ):
                if chunk.content:
                    full_content += chunk.content
                    yield {"type": "delta", "content": chunk.content}
                if chunk.is_final:
                    tokens_used = chunk.tokens_used or 0
        except Exception as e:
            logger.error(f"Coding AI streaming failed: {e}")
            generation_error = True
            error_msg = "Извините, произошла ошибка. Попробуйте позже." if language == "ru" \
                else "Кешіріңіз, қате орын алды. Кейінірек қайталап көріңіз."
            yield {"type": "error", "error": error_msg}
            if not full_content:
                full_content = error_msg

        processing_time = int((time.time() - start_time) * 1000)

        # Save assistant message
        assistant_message = ChatMessage(
            session_id=session.id,
            school_id=school_id,
            role="assistant",
            content=full_content,
            tokens_used=tokens_used,
            model_used=self.llm.provider,
            processing_time_ms=processing_time,
        )
        self.db.add(assistant_message)

        # Update session stats
        was_first = session.message_count == 0
        session.message_count += 2
        session.total_tokens_used += tokens_used
        session.last_message_at = datetime.utcnow()
        if was_first:
            session.title = f"AI Help: {challenge.title[:60]}"

        await self.db.commit()
        await self.db.refresh(assistant_message)
        await self.db.refresh(session)

        # Log usage
        try:
            usage_ctx = LLMUsageContext(
                db=self.db, feature=LLMFeature.CODING_CHAT.value,
                user_id=student_id, student_id=student_id, school_id=school_id,
            )
            response = LLMResponse(
                content=full_content, model=self.llm.provider,
                tokens_used=tokens_used,
            )
            await self.llm._log_usage(usage_ctx, response, processing_time)
        except Exception as e:
            logger.warning(f"Failed to log coding chat usage: {e}")

        done_event: Dict[str, Any] = {
            "type": "done",
            "message": _message_to_dict(assistant_message),
            "session": _session_to_dict(session),
        }
        if generation_error:
            done_event["generation_error"] = True
        yield done_event

    async def send_followup_stream(
        self,
        session_id: int,
        student_id: int,
        school_id: int,
        content: str,
        code: Optional[str] = None,
        error: Optional[str] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Send a follow-up message in an existing coding chat session."""
        start_time = time.time()
        await self._ensure_rls_context(school_id)

        session = await self.get_session_with_messages(session_id, student_id, school_id)
        if not session:
            yield {"type": "error", "error": f"Session {session_id} not found"}
            return

        # Load challenge for system prompt
        challenge = await self.db.get(CodingChallenge, session.challenge_id)
        if not challenge:
            yield {"type": "error", "error": "Challenge not found"}
            return

        # Build user message with optional code context
        user_content = content
        if code:
            user_content += f"\n\nМой текущий код:\n```python\n{code}\n```"
        if error:
            user_content += f"\n\nОшибка:\n```\n{error}\n```"

        # Save user message
        user_message = ChatMessage(
            session_id=session.id,
            school_id=school_id,
            role="user",
            content=user_content,
        )
        self.db.add(user_message)
        await self.db.flush()

        yield {
            "type": "user_message",
            "message": _message_to_dict(user_message),
        }

        # Build LLM messages
        system_prompt = self._build_system_prompt(challenge, session.language)
        messages = self._build_llm_messages(session, system_prompt, user_content)

        # Stream
        full_content = ""
        tokens_used = 0
        generation_error = False

        try:
            async for chunk in self.llm.stream_generate(
                messages=messages, temperature=0.7, max_tokens=1500,
            ):
                if chunk.content:
                    full_content += chunk.content
                    yield {"type": "delta", "content": chunk.content}
                if chunk.is_final:
                    tokens_used = chunk.tokens_used or 0
        except Exception as e:
            logger.error(f"Coding AI follow-up streaming failed: {e}")
            generation_error = True
            yield {"type": "error", "error": "Ошибка генерации. Попробуйте позже."}
            if not full_content:
                full_content = "Ошибка генерации."

        processing_time = int((time.time() - start_time) * 1000)

        assistant_message = ChatMessage(
            session_id=session.id,
            school_id=school_id,
            role="assistant",
            content=full_content,
            tokens_used=tokens_used,
            model_used=self.llm.provider,
            processing_time_ms=processing_time,
        )
        self.db.add(assistant_message)

        session.message_count += 2
        session.total_tokens_used += tokens_used
        session.last_message_at = datetime.utcnow()

        await self.db.commit()
        await self.db.refresh(assistant_message)
        await self.db.refresh(session)

        done_event: Dict[str, Any] = {
            "type": "done",
            "message": _message_to_dict(assistant_message),
            "session": _session_to_dict(session),
        }
        if generation_error:
            done_event["generation_error"] = True
        yield done_event

    # =========================================================================
    # Prompt Construction
    # =========================================================================

    def _build_system_prompt(self, challenge: CodingChallenge, language: str) -> str:
        """Build coding-specific system prompt with challenge context."""
        template = SYSTEM_PROMPTS.get(language, SYSTEM_PROMPTS["ru"])

        # Use localized title/description if available
        if language == "kk" and challenge.title_kk:
            title = challenge.title_kk
            description = challenge.description_kk or challenge.description
        else:
            title = challenge.title
            description = challenge.description

        difficulty_labels = {
            "easy": "Лёгкая" if language == "ru" else "Жеңіл",
            "medium": "Средняя" if language == "ru" else "Орташа",
            "hard": "Сложная" if language == "ru" else "Күрделі",
        }

        return template.format(
            title=title,
            description=description[:2000],
            difficulty=difficulty_labels.get(challenge.difficulty, challenge.difficulty),
        )

    def _format_action_message(
        self,
        action: CodingAction,
        code: str,
        language: str,
        error: Optional[str] = None,
        test_results: Optional[str] = None,
    ) -> str:
        """Format action-specific user message for LLM."""
        # Truncate code to prevent excessive tokens
        truncated_code = code[:3000] if len(code) > 3000 else code

        if action == CodingAction.FREE_CHAT:
            return truncated_code  # For free_chat, code field contains the message

        templates = ACTION_PROMPTS.get(action, ACTION_PROMPTS[CodingAction.HINT])
        template = templates.get(language, templates["ru"])

        error_block = ""
        if error:
            truncated_error = error[:2000] if len(error) > 2000 else error
            if language == "kk":
                error_block = f"\nҚате:\n```\n{truncated_error}\n```"
            else:
                error_block = f"\nОшибка:\n```\n{truncated_error}\n```"

        test_block = ""
        if test_results:
            truncated_tests = test_results[:2000] if len(test_results) > 2000 else test_results
            if language == "kk":
                test_block = f"\nТест нәтижелері:\n{truncated_tests}"
            else:
                test_block = f"\nРезультаты тестов:\n{truncated_tests}"

        return template.format(
            code=truncated_code,
            error=error[:2000] if error else "",
            error_block=error_block,
            test_block=test_block,
        )

    def _build_llm_messages(
        self,
        session: ChatSession,
        system_prompt: str,
        current_message: str,
    ) -> List[dict]:
        """Build messages array: system + history + current user message."""
        messages = [{"role": "system", "content": system_prompt}]

        # Add conversation history (last N messages)
        if hasattr(session, "messages") and session.messages:
            for msg in session.messages[-MAX_HISTORY_MESSAGES:]:
                if not msg.is_deleted:
                    messages.append({"role": msg.role, "content": msg.content})

        messages.append({"role": "user", "content": current_message})
        return messages


# =============================================================================
# Helper functions (module-level to keep service lean)
# =============================================================================

def _message_to_dict(message: ChatMessage) -> dict:
    """Convert ChatMessage to JSON-serializable dict."""
    return {
        "id": message.id,
        "role": message.role,
        "content": message.content,
        "tokens_used": message.tokens_used,
        "model_used": message.model_used,
        "processing_time_ms": message.processing_time_ms,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }


def _session_to_dict(session: ChatSession) -> dict:
    """Convert ChatSession to JSON-serializable dict."""
    return {
        "id": session.id,
        "session_type": session.session_type,
        "challenge_id": session.challenge_id,
        "title": session.title,
        "language": session.language,
        "message_count": session.message_count,
        "total_tokens_used": session.total_tokens_used,
        "last_message_at": session.last_message_at.isoformat() if session.last_message_at else None,
        "created_at": session.created_at.isoformat() if session.created_at else None,
    }
