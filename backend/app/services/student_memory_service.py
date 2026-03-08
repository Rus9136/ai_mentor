"""
Student Memory Service for AI chat personalization.

Provides 3-layer memory:
1. Short-term: last 10 messages (handled by ChatService)
2. Session memory: LLM-generated session summaries
3. Long-term: structured learner profile, updated incrementally

All extraction runs as background tasks after chat responses.
"""
import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Optional

from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.chat import ChatSession, ChatMessage
from app.models.student_memory import ChatSessionSummary, StudentMemory
from app.services.llm_service import LLMService, LLMUsageContext

logger = logging.getLogger(__name__)

# Maximum tokens for memory context in system prompt
MAX_MEMORY_CHARS = 3200
MAX_SESSION_SUMMARIES = 5
MIN_MESSAGES_FOR_SUMMARY = 4


# =========================================================================
# 1. Load memory for prompt injection
# =========================================================================

async def load_memory_context(db: AsyncSession, student_id: int) -> Optional[str]:
    """
    Load student memory and recent session summaries for LLM context.

    Returns formatted text block to inject into system prompt,
    or None if no memory exists yet.
    """
    # Load long-term memory
    result = await db.execute(
        select(StudentMemory).where(StudentMemory.student_id == student_id)
    )
    memory = result.scalar_one_or_none()

    # Load recent session summaries
    result = await db.execute(
        select(ChatSessionSummary)
        .where(ChatSessionSummary.student_id == student_id)
        .order_by(ChatSessionSummary.created_at.desc())
        .limit(MAX_SESSION_SUMMARIES)
    )
    summaries = list(result.scalars().all())

    if not memory and not summaries:
        return None

    lines = ["--- ПРОФИЛЬ УЧЕНИКА ---"]

    # Format long-term memory
    if memory and memory.memory_data:
        data = memory.memory_data
        if data.get("learning_style"):
            lines.append(f"Стиль обучения: {data['learning_style']}")
        if data.get("strong_topics"):
            topics = ", ".join(data["strong_topics"][:5])
            lines.append(f"Сильные темы: {topics}")
        if data.get("weak_topics"):
            topics = ", ".join(data["weak_topics"][:5])
            lines.append(f"Слабые темы: {topics}")
        if data.get("misconceptions"):
            items = ", ".join(data["misconceptions"][:3])
            lines.append(f"Заблуждения: {items}")
        if data.get("preferred_explanation_style"):
            lines.append(f"Предпочтения: {data['preferred_explanation_style']}")
        if data.get("interests"):
            items = ", ".join(data["interests"][:5])
            lines.append(f"Интересы: {items}")
        if data.get("notes"):
            lines.append(f"Заметки: {data['notes'][:200]}")

    # Format session summaries (most recent first)
    if summaries:
        lines.append("")
        lines.append("ПРЕДЫДУЩИЕ СЕССИИ:")
        for i, s in enumerate(summaries, 1):
            date_str = s.created_at.strftime("%d.%m") if s.created_at else "?"
            conf = f" (уверенность: {s.confidence_level})" if s.confidence_level else ""
            topic = s.topic or "общие вопросы"
            summary_text = s.summary[:150] if s.summary else ""
            lines.append(f"{i}. [{date_str}] {topic} — {summary_text}{conf}")

    lines.append("")
    lines.append(
        "ИНСТРУКЦИЯ: Используй информацию о профиле для персонализации ответов. "
        "Не упоминай ученику что у тебя есть память о нём."
    )

    context = "\n".join(lines)

    # Enforce token budget
    if len(context) > MAX_MEMORY_CHARS:
        context = context[:MAX_MEMORY_CHARS] + "\n..."

    return context


# =========================================================================
# 2. Session summarization (background)
# =========================================================================

def _parse_llm_json(content: str) -> Optional[dict]:
    """Parse JSON from LLM response, handling markdown code fences."""
    content = content.strip()
    # Strip markdown code fences
    content = re.sub(r'^```(?:json)?\s*\n?', '', content)
    content = re.sub(r'\n?```\s*$', '', content)
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        logger.warning(f"Failed to parse LLM JSON: {content[:200]}")
        return None


async def _summarize_session(
    session_id: int,
    student_id: int,
    school_id: int,
    db: AsyncSession
) -> Optional[ChatSessionSummary]:
    """Generate and save a session summary using LLM."""

    # Check if summary already exists (idempotent)
    existing = await db.execute(
        select(ChatSessionSummary).where(
            ChatSessionSummary.session_id == session_id
        )
    )
    if existing.scalar_one_or_none():
        logger.debug(f"Summary already exists for session {session_id}")
        return None

    # Load session messages
    result = await db.execute(
        select(ChatMessage)
        .where(
            ChatMessage.session_id == session_id,
            ChatMessage.is_deleted == False
        )
        .order_by(ChatMessage.created_at)
    )
    messages = list(result.scalars().all())

    if len(messages) < MIN_MESSAGES_FOR_SUMMARY:
        logger.debug(f"Session {session_id} has {len(messages)} messages, skipping summary")
        return None

    # Build conversation text
    conversation_lines = []
    for msg in messages:
        role_label = "Ученик" if msg.role == "user" else "Репетитор"
        conversation_lines.append(f"{role_label}: {msg.content[:500]}")
    conversation_text = "\n".join(conversation_lines)

    # LLM prompt
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "Ты анализируешь разговор между учеником и ИИ-репетитором. "
                "Создай краткую сводку. Отвечай ТОЛЬКО валидным JSON."
            )
        },
        {
            "role": "user",
            "content": f"""Проанализируй этот разговор и верни JSON:

{{
  "topic": "основная тема разговора (кратко)",
  "summary": "2-3 предложения: что обсуждали, что ученик понял/не понял",
  "knowledge_gaps": ["список тем, где ученик затруднялся"],
  "confidence_level": "low или medium или high"
}}

Разговор:
{conversation_text[:3000]}"""
        }
    ]

    llm = LLMService()
    usage_ctx = LLMUsageContext(
        db=db,
        feature="memory",
        student_id=student_id,
        school_id=school_id,
    )

    response = await llm.generate(
        messages=prompt_messages,
        temperature=0.3,
        max_tokens=500,
        usage_context=usage_ctx,
    )

    parsed = _parse_llm_json(response.content)
    if not parsed:
        logger.error(f"Failed to parse session summary for session {session_id}")
        return None

    summary = ChatSessionSummary(
        session_id=session_id,
        student_id=student_id,
        school_id=school_id,
        topic=parsed.get("topic", "")[:255],
        summary=parsed.get("summary", ""),
        knowledge_gaps=parsed.get("knowledge_gaps", []),
        confidence_level=parsed.get("confidence_level", "medium"),
        message_count=len(messages),
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    logger.info(f"Created session summary for session {session_id}: topic='{summary.topic}'")
    return summary


# =========================================================================
# 3. Long-term memory update (background)
# =========================================================================

async def _update_student_memory(
    session_id: int,
    student_id: int,
    school_id: int,
    db: AsyncSession
) -> None:
    """Update long-term student memory based on latest session summary."""

    # Load session summary
    result = await db.execute(
        select(ChatSessionSummary).where(
            ChatSessionSummary.session_id == session_id
        )
    )
    summary = result.scalar_one_or_none()
    if not summary:
        return

    # Load existing memory
    result = await db.execute(
        select(StudentMemory).where(StudentMemory.student_id == student_id)
    )
    existing_memory = result.scalar_one_or_none()

    existing_data = existing_memory.memory_data if existing_memory else {}
    existing_json = json.dumps(existing_data, ensure_ascii=False) if existing_data else "Профиль пока пуст — это первый разговор."

    # LLM prompt
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "Ты анализируешь данные об ученике для обновления его профиля. "
                "Сохраняй накопленные данные, добавляй новые наблюдения. "
                "Отвечай ТОЛЬКО валидным JSON."
            )
        },
        {
            "role": "user",
            "content": f"""Текущий профиль ученика:
{existing_json}

Новая сессия:
Тема: {summary.topic}
Сводка: {summary.summary}
Пробелы в знаниях: {json.dumps(summary.knowledge_gaps, ensure_ascii=False)}
Уверенность: {summary.confidence_level}

Обнови профиль. Верни JSON (сохрани существующие данные, добавь новые):
{{
  "learning_style": "стиль обучения ученика",
  "weak_topics": ["темы, где ученик слаб"],
  "strong_topics": ["темы, которые ученик освоил"],
  "preferred_explanation_style": "как ученику лучше объяснять",
  "misconceptions": ["заблуждения ученика"],
  "interests": ["интересы ученика"],
  "notes": "общие наблюдения о ученике"
}}"""
        }
    ]

    llm = LLMService()
    usage_ctx = LLMUsageContext(
        db=db,
        feature="memory",
        student_id=student_id,
        school_id=school_id,
    )

    response = await llm.generate(
        messages=prompt_messages,
        temperature=0.3,
        max_tokens=600,
        usage_context=usage_ctx,
    )

    parsed = _parse_llm_json(response.content)
    if not parsed:
        logger.error(f"Failed to parse memory update for student {student_id}")
        return

    if existing_memory:
        existing_memory.memory_data = parsed
        existing_memory.extraction_count += 1
        existing_memory.last_session_id = session_id
        existing_memory.updated_at = datetime.utcnow()
    else:
        new_memory = StudentMemory(
            student_id=student_id,
            school_id=school_id,
            memory_data=parsed,
            extraction_count=1,
            last_session_id=session_id,
        )
        db.add(new_memory)

    await db.commit()
    logger.info(f"Updated student memory for student {student_id}")


# =========================================================================
# 4. Background trigger
# =========================================================================

async def _run_memory_extraction(
    session_id: int,
    student_id: int,
    school_id: int
) -> None:
    """Run session summarization and memory update in background."""
    try:
        async with AsyncSessionLocal() as db:
            # Set RLS context for background task
            await db.execute(sa_text(f"SET app.current_tenant_id = '{school_id}'"))
            await db.execute(sa_text(f"SET app.current_school_id = '{school_id}'"))
            summary = await _summarize_session(session_id, student_id, school_id, db)
            if summary:
                await _update_student_memory(session_id, student_id, school_id, db)
    except Exception:
        logger.exception(
            f"Memory extraction failed for session {session_id}, student {student_id}"
        )


def trigger_memory_extraction(
    session_id: int,
    student_id: int,
    school_id: int
) -> None:
    """Fire-and-forget trigger for background memory extraction."""
    asyncio.create_task(
        _run_memory_extraction(session_id, student_id, school_id)
    )
    logger.info(f"Triggered memory extraction for session {session_id}")
