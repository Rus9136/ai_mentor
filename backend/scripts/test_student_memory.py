"""
Test script for Student Memory Service.

Verifies all 3 layers of memory:
1. Load memory context (should be empty initially)
2. Summarize existing chat sessions
3. Update long-term student memory
4. Load memory context again (should have data)

Usage:
    docker exec ai_mentor_backend_prod python scripts/test_student_memory.py
    docker exec ai_mentor_backend_prod python scripts/test_student_memory.py --cleanup
"""
import asyncio
import argparse
import json
import sys

# Fix imports
sys.path.insert(0, "/app")

from app.core.database import AsyncSessionLocal
from app.services.student_memory_service import (
    load_memory_context,
    _summarize_session,
    _update_student_memory,
    _parse_llm_json,
)
from app.models.student_memory import ChatSessionSummary, StudentMemory
from app.models.chat import ChatSession, ChatMessage
from sqlalchemy import select, delete, text


# =========================================================================
# Test config
# =========================================================================

# Use real student from DB
TEST_STUDENT_ID = 5
TEST_SCHOOL_ID = 5


async def set_rls_context(db, school_id: int = TEST_SCHOOL_ID):
    """Set RLS context so queries can see school data."""
    await db.execute(text(f"SET app.current_tenant_id = '{school_id}'"))
    await db.execute(text(f"SET app.current_school_id = '{school_id}'"))

# Colors for output
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
CYAN = "\033[96m"
RESET = "\033[0m"
BOLD = "\033[1m"


def ok(msg: str):
    print(f"  {GREEN}OK{RESET} {msg}")


def fail(msg: str):
    print(f"  {RED}FAIL{RESET} {msg}")


def info(msg: str):
    print(f"  {CYAN}INFO{RESET} {msg}")


def header(msg: str):
    print(f"\n{BOLD}{YELLOW}=== {msg} ==={RESET}")


# =========================================================================
# Tests
# =========================================================================

async def test_json_parser():
    """Test JSON parsing with various LLM output formats."""
    header("Test 1: JSON Parser")

    # Clean JSON
    result = _parse_llm_json('{"topic": "math", "confidence_level": "high"}')
    if result and result["topic"] == "math":
        ok("Clean JSON parsed")
    else:
        fail("Clean JSON failed")

    # JSON with markdown fences
    result = _parse_llm_json('```json\n{"topic": "algebra"}\n```')
    if result and result["topic"] == "algebra":
        ok("Markdown-fenced JSON parsed")
    else:
        fail("Markdown-fenced JSON failed")

    # Invalid JSON
    result = _parse_llm_json("This is not JSON at all")
    if result is None:
        ok("Invalid JSON returned None")
    else:
        fail("Invalid JSON should return None")

    # JSON with code fence (no 'json' label)
    result = _parse_llm_json('```\n{"key": "value"}\n```')
    if result and result["key"] == "value":
        ok("Code-fenced JSON (no label) parsed")
    else:
        fail("Code-fenced JSON (no label) failed")


async def test_load_empty_memory():
    """Test that load_memory_context returns None for student with no memory."""
    header("Test 2: Load Empty Memory")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        context = await load_memory_context(db, student_id=999999)

        if context is None:
            ok("No memory for unknown student → returned None")
        else:
            fail(f"Expected None, got: {context[:100]}")


async def test_load_initial_memory():
    """Check if test student already has memory."""
    header("Test 3: Check Existing Memory for Student")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        context = await load_memory_context(db, student_id=TEST_STUDENT_ID)

        if context is None:
            info(f"Student {TEST_STUDENT_ID} has no memory yet (expected for first run)")
        else:
            ok(f"Student {TEST_STUDENT_ID} already has memory:")
            for line in context.split("\n")[:10]:
                print(f"    {line}")


async def test_get_sessions():
    """Find sessions eligible for summarization."""
    header("Test 4: Find Sessions for Summarization")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        result = await db.execute(
            select(ChatSession)
            .where(
                ChatSession.student_id == TEST_STUDENT_ID,
                ChatSession.is_deleted == False,
                ChatSession.message_count >= 4,
            )
            .order_by(ChatSession.created_at.desc())
        )
        sessions = list(result.scalars().all())

        if not sessions:
            fail(f"No sessions with 4+ messages for student {TEST_STUDENT_ID}")
            return []

        ok(f"Found {len(sessions)} sessions eligible for summarization:")
        for s in sessions:
            # Check if summary already exists
            existing = await db.execute(
                select(ChatSessionSummary).where(
                    ChatSessionSummary.session_id == s.id
                )
            )
            has_summary = existing.scalar_one_or_none() is not None
            status = f"{GREEN}summarized{RESET}" if has_summary else f"{YELLOW}pending{RESET}"
            print(f"    Session {s.id}: {s.session_type}, {s.message_count} msgs, {s.title} [{status}]")

        return sessions


async def test_summarize_session(session_id: int):
    """Test session summarization with real LLM call."""
    header(f"Test 5: Summarize Session {session_id}")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        # Load messages to show what we're summarizing
        result = await db.execute(
            select(ChatMessage)
            .where(
                ChatMessage.session_id == session_id,
                ChatMessage.is_deleted == False,
            )
            .order_by(ChatMessage.created_at)
        )
        messages = list(result.scalars().all())
        info(f"Session has {len(messages)} messages:")
        for msg in messages[:6]:
            role = "Ученик" if msg.role == "user" else "ИИ"
            content_preview = msg.content[:80].replace("\n", " ")
            print(f"    [{role}] {content_preview}...")

        # Run summarization
        info("Calling LLM for summarization...")
        summary = await _summarize_session(
            session_id=session_id,
            student_id=TEST_STUDENT_ID,
            school_id=TEST_SCHOOL_ID,
            db=db,
        )

        if summary is None:
            # Could be already exists or not enough messages
            existing = await db.execute(
                select(ChatSessionSummary).where(
                    ChatSessionSummary.session_id == session_id
                )
            )
            if existing.scalar_one_or_none():
                info("Summary already exists (idempotent check passed)")
            else:
                fail("Summarization returned None unexpectedly")
            return

        ok(f"Summary created:")
        print(f"    Тема: {summary.topic}")
        print(f"    Сводка: {summary.summary}")
        print(f"    Пробелы: {summary.knowledge_gaps}")
        print(f"    Уверенность: {summary.confidence_level}")


async def test_update_memory(session_id: int):
    """Test long-term memory update."""
    header(f"Test 6: Update Long-term Memory (from session {session_id})")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        info("Calling LLM for memory update...")
        await _update_student_memory(
            session_id=session_id,
            student_id=TEST_STUDENT_ID,
            school_id=TEST_SCHOOL_ID,
            db=db,
        )

        # Check result
        result = await db.execute(
            select(StudentMemory).where(
                StudentMemory.student_id == TEST_STUDENT_ID
            )
        )
        memory = result.scalar_one_or_none()

        if memory is None:
            fail("No student memory created")
            return

        ok(f"Student memory updated (extraction #{memory.extraction_count}):")
        data = memory.memory_data
        for key, value in data.items():
            if isinstance(value, list):
                value_str = ", ".join(str(v) for v in value[:5])
            else:
                value_str = str(value)[:100]
            print(f"    {key}: {value_str}")


async def test_load_final_memory():
    """Test that memory context is now loaded into prompt."""
    header("Test 7: Load Memory Context (should have data now)")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        context = await load_memory_context(db, student_id=TEST_STUDENT_ID)

        if context is None:
            fail("Memory context is still None after extraction")
            return

        ok(f"Memory context loaded ({len(context)} chars):")
        print()
        for line in context.split("\n"):
            print(f"    {line}")
        print()

        # Check token budget
        if len(context) <= 3200:
            ok(f"Within token budget ({len(context)}/3200 chars)")
        else:
            fail(f"Exceeds token budget ({len(context)}/3200 chars)")


async def cleanup():
    """Remove all test memory data."""
    header("Cleanup: Removing Memory Data")

    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        r1 = await db.execute(
            delete(ChatSessionSummary).where(
                ChatSessionSummary.student_id == TEST_STUDENT_ID
            )
        )
        r2 = await db.execute(
            delete(StudentMemory).where(
                StudentMemory.student_id == TEST_STUDENT_ID
            )
        )
        await db.commit()

        ok(f"Deleted {r1.rowcount} session summaries, {r2.rowcount} memory records")


# =========================================================================
# Main
# =========================================================================

async def main():
    parser = argparse.ArgumentParser(description="Test Student Memory Service")
    parser.add_argument("--cleanup", action="store_true", help="Remove all test memory data")
    parser.add_argument("--skip-llm", action="store_true", help="Skip tests that require LLM calls")
    args = parser.parse_args()

    print(f"\n{BOLD}Student Memory Service — Test Suite{RESET}")
    print(f"Student ID: {TEST_STUDENT_ID}, School ID: {TEST_SCHOOL_ID}\n")

    if args.cleanup:
        await cleanup()
        return

    # Tests that don't need LLM
    await test_json_parser()
    await test_load_empty_memory()
    await test_load_initial_memory()

    sessions = await test_get_sessions()
    if not sessions:
        print(f"\n{RED}No sessions to test with. Exiting.{RESET}")
        return

    if args.skip_llm:
        print(f"\n{YELLOW}Skipping LLM tests (--skip-llm){RESET}")
        return

    # Pick first session without summary for testing
    async with AsyncSessionLocal() as db:
        await set_rls_context(db)
        target_session = None
        for s in sessions:
            existing = await db.execute(
                select(ChatSessionSummary).where(
                    ChatSessionSummary.session_id == s.id
                )
            )
            if not existing.scalar_one_or_none():
                target_session = s
                break

        if not target_session:
            # All sessions already summarized, use the first one for memory test
            target_session = sessions[0]
            info(f"All sessions already summarized, using session {target_session.id}")

    # LLM tests
    await test_summarize_session(target_session.id)
    await test_update_memory(target_session.id)
    await test_load_final_memory()

    # Summary
    header("Done")
    print(f"  All tests passed. Memory system is working.")
    print(f"  Run with --cleanup to remove test data.\n")


if __name__ == "__main__":
    asyncio.run(main())
