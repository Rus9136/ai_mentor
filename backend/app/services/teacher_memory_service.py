"""
Teacher Memory Service for AI chat personalization.

Provides 3-layer memory for teacher chat:
1. Short-term: last 10 messages (handled by ChatService)
2. Session memory: LLM-generated session summaries
3. Long-term: structured teacher profile, updated incrementally

All extraction runs as background tasks after chat responses.
"""
import asyncio
import json
import logging
from datetime import datetime
from typing import Optional

from sqlalchemy import select, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.chat import ChatSession, ChatMessage
from app.models.teacher_memory import TeacherChatSessionSummary, TeacherMemory
from app.services.llm_service import LLMService, LLMUsageContext
from app.services.student_memory_service import _parse_llm_json

logger = logging.getLogger(__name__)

MAX_MEMORY_CHARS = 3200
MAX_SESSION_SUMMARIES = 5
MIN_MESSAGES_FOR_SUMMARY = 4


# =========================================================================
# 1. Load memory for prompt injection
# =========================================================================

async def load_teacher_memory_context(db: AsyncSession, teacher_id: int) -> Optional[str]:
    """
    Load teacher memory and recent session summaries for LLM context.

    Returns formatted text block to inject into system prompt,
    or None if no memory exists yet.
    """
    # Load long-term memory
    result = await db.execute(
        select(TeacherMemory).where(TeacherMemory.teacher_id == teacher_id)
    )
    memory = result.scalar_one_or_none()

    # Load recent session summaries
    result = await db.execute(
        select(TeacherChatSessionSummary)
        .where(TeacherChatSessionSummary.teacher_id == teacher_id)
        .order_by(TeacherChatSessionSummary.created_at.desc())
        .limit(MAX_SESSION_SUMMARIES)
    )
    summaries = list(result.scalars().all())

    if not memory and not summaries:
        return None

    lines = ["--- ПРОФИЛЬ УЧИТЕЛЯ ---"]

    # Format long-term memory
    if memory and memory.memory_data:
        data = memory.memory_data
        if data.get("teaching_style"):
            lines.append(f"Стиль преподавания: {data['teaching_style']}")
        if data.get("frequent_topics"):
            topics = ", ".join(data["frequent_topics"][:5])
            lines.append(f"Частые темы: {topics}")
        if data.get("preferred_preparation_style"):
            lines.append(f"Подготовка к урокам: {data['preferred_preparation_style']}")
        if data.get("methodological_preferences"):
            items = ", ".join(data["methodological_preferences"][:5])
            lines.append(f"Методические предпочтения: {items}")
        if data.get("subject_expertise"):
            items = ", ".join(data["subject_expertise"][:5])
            lines.append(f"Предметная экспертиза: {items}")
        if data.get("common_requests"):
            items = ", ".join(data["common_requests"][:5])
            lines.append(f"Типичные запросы: {items}")
        if data.get("notes"):
            lines.append(f"Заметки: {data['notes'][:200]}")

    # Format session summaries (most recent first)
    if summaries:
        lines.append("")
        lines.append("ПРЕДЫДУЩИЕ СЕССИИ:")
        for i, s in enumerate(summaries, 1):
            date_str = s.created_at.strftime("%d.%m") if s.created_at else "?"
            stype = f" (тип: {s.session_type})" if s.session_type else ""
            topic = s.topic or "общие вопросы"
            summary_text = s.summary[:150] if s.summary else ""
            lines.append(f"{i}. [{date_str}] {topic} — {summary_text}{stype}")

    lines.append("")
    lines.append(
        "ИНСТРУКЦИЯ: Используй информацию о профиле учителя для персонализации ответов. "
        "Не упоминай учителю что у тебя есть память о нём."
    )

    context = "\n".join(lines)

    # Enforce token budget
    if len(context) > MAX_MEMORY_CHARS:
        context = context[:MAX_MEMORY_CHARS] + "\n..."

    return context


# =========================================================================
# 2. Session summarization (background)
# =========================================================================

async def _summarize_teacher_session(
    session_id: int,
    teacher_id: int,
    school_id: int,
    db: AsyncSession
) -> Optional[TeacherChatSessionSummary]:
    """Generate and save a teacher session summary using LLM."""

    # Check if summary already exists (idempotent)
    existing = await db.execute(
        select(TeacherChatSessionSummary).where(
            TeacherChatSessionSummary.session_id == session_id
        )
    )
    if existing.scalar_one_or_none():
        logger.debug(f"Teacher summary already exists for session {session_id}")
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
        logger.debug(f"Teacher session {session_id} has {len(messages)} messages, skipping summary")
        return None

    # Build conversation text
    conversation_lines = []
    for msg in messages:
        role_label = "Учитель" if msg.role == "user" else "Ассистент"
        conversation_lines.append(f"{role_label}: {msg.content[:500]}")
    conversation_text = "\n".join(conversation_lines)

    # LLM prompt
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "Ты анализируешь разговор между учителем и ИИ-ассистентом. "
                "Создай краткую сводку. Отвечай ТОЛЬКО валидным JSON."
            )
        },
        {
            "role": "user",
            "content": f"""Проанализируй этот разговор и верни JSON:

{{
  "topic": "основная тема разговора (кратко)",
  "summary": "2-3 предложения: что обсуждали, какие решения нашли",
  "key_insights": ["методические находки или полезные идеи из разговора"],
  "session_type": "preparation или methodology или assessment или content_review"
}}

Разговор:
{conversation_text[:3000]}"""
        }
    ]

    llm = LLMService()
    usage_ctx = LLMUsageContext(
        db=db,
        feature="memory",
        teacher_id=teacher_id,
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
        logger.error(f"Failed to parse teacher session summary for session {session_id}")
        return None

    summary = TeacherChatSessionSummary(
        session_id=session_id,
        teacher_id=teacher_id,
        school_id=school_id,
        topic=parsed.get("topic", "")[:255],
        summary=parsed.get("summary", ""),
        key_insights=parsed.get("key_insights", []),
        session_type=parsed.get("session_type", "content_review")[:30],
        message_count=len(messages),
    )
    db.add(summary)
    await db.commit()
    await db.refresh(summary)

    logger.info(f"Created teacher session summary for session {session_id}: topic='{summary.topic}'")
    return summary


# =========================================================================
# 3. Long-term memory update (background)
# =========================================================================

async def _update_teacher_memory(
    session_id: int,
    teacher_id: int,
    school_id: int,
    db: AsyncSession
) -> None:
    """Update long-term teacher memory based on latest session summary."""

    # Load session summary
    result = await db.execute(
        select(TeacherChatSessionSummary).where(
            TeacherChatSessionSummary.session_id == session_id
        )
    )
    summary = result.scalar_one_or_none()
    if not summary:
        return

    # Load existing memory
    result = await db.execute(
        select(TeacherMemory).where(TeacherMemory.teacher_id == teacher_id)
    )
    existing_memory = result.scalar_one_or_none()

    existing_data = existing_memory.memory_data if existing_memory else {}
    existing_json = json.dumps(existing_data, ensure_ascii=False) if existing_data else "Профиль пока пуст — это первый разговор."

    # LLM prompt
    prompt_messages = [
        {
            "role": "system",
            "content": (
                "Ты анализируешь данные об учителе для обновления его профиля. "
                "Сохраняй накопленные данные, добавляй новые наблюдения. "
                "Отвечай ТОЛЬКО валидным JSON."
            )
        },
        {
            "role": "user",
            "content": f"""Текущий профиль учителя:
{existing_json}

Новая сессия:
Тема: {summary.topic}
Сводка: {summary.summary}
Ключевые инсайты: {json.dumps(summary.key_insights, ensure_ascii=False)}
Тип сессии: {summary.session_type}

Обнови профиль. Верни JSON (сохрани существующие данные, добавь новые):
{{
  "teaching_style": "стиль преподавания учителя",
  "frequent_topics": ["темы, которые учитель часто обсуждает"],
  "preferred_preparation_style": "как учитель предпочитает готовиться к урокам",
  "methodological_preferences": ["методические приёмы и подходы"],
  "subject_expertise": ["предметные области"],
  "common_requests": ["типичные запросы к ИИ-ассистенту"],
  "notes": "общие наблюдения об учителе"
}}"""
        }
    ]

    llm = LLMService()
    usage_ctx = LLMUsageContext(
        db=db,
        feature="memory",
        teacher_id=teacher_id,
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
        logger.error(f"Failed to parse memory update for teacher {teacher_id}")
        return

    if existing_memory:
        existing_memory.memory_data = parsed
        existing_memory.extraction_count += 1
        existing_memory.last_session_id = session_id
        existing_memory.updated_at = datetime.utcnow()
    else:
        new_memory = TeacherMemory(
            teacher_id=teacher_id,
            school_id=school_id,
            memory_data=parsed,
            extraction_count=1,
            last_session_id=session_id,
        )
        db.add(new_memory)

    await db.commit()
    logger.info(f"Updated teacher memory for teacher {teacher_id}")


# =========================================================================
# 4. Background trigger
# =========================================================================

async def _run_teacher_memory_extraction(
    session_id: int,
    teacher_id: int,
    school_id: int
) -> None:
    """Run teacher session summarization and memory update in background."""
    try:
        async with AsyncSessionLocal() as db:
            # Set RLS context for background task
            await db.execute(sa_text(f"SET app.current_tenant_id = '{school_id}'"))
            await db.execute(sa_text(f"SET app.current_school_id = '{school_id}'"))
            summary = await _summarize_teacher_session(session_id, teacher_id, school_id, db)
            if summary:
                await _update_teacher_memory(session_id, teacher_id, school_id, db)
    except Exception:
        logger.exception(
            f"Teacher memory extraction failed for session {session_id}, teacher {teacher_id}"
        )


def trigger_teacher_memory_extraction(
    session_id: int,
    teacher_id: int,
    school_id: int
) -> None:
    """Fire-and-forget trigger for background teacher memory extraction."""
    asyncio.create_task(
        _run_teacher_memory_extraction(session_id, teacher_id, school_id)
    )
    logger.info(f"Triggered teacher memory extraction for session {session_id}")
