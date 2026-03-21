"""
Student-facing API endpoints for coding AI mentor.

Routes:
  POST /coding/ai/start                          — Start AI action (SSE streaming)
  POST /coding/ai/sessions/{id}/messages/stream   — Follow-up message (SSE streaming)
  GET  /coding/ai/sessions/{id}                   — Get session with messages
  GET  /coding/ai/challenge/{challenge_id}/session — Find active session for challenge
"""
import json
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    get_current_user_school_id,
    get_student_from_user,
)
from app.models.student import Student
from app.models.coding import CodingChallenge
from app.services.coding_chat_service import CodingChatService
from app.schemas.coding_chat import CodingChatStartRequest, CodingChatMessageRequest

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/coding/ai")


# ---------------------------------------------------------------------------
# Start AI Action (streaming)
# ---------------------------------------------------------------------------

@router.post("/start", summary="Start AI mentor action on a coding challenge")
async def start_coding_ai(
    request: CodingChatStartRequest,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Start an AI mentor action (hint, explain_error, code_review, step_by_step).

    Returns SSE stream with events:
    - user_message: The formatted user message
    - delta: Partial AI response content
    - done: Final message with session metadata
    - error: Error message if something fails
    """
    # Validate challenge exists
    challenge = await db.get(CodingChallenge, request.challenge_id)
    if not challenge:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Challenge {request.challenge_id} not found",
        )

    service = CodingChatService(db)

    async def event_generator():
        try:
            async for event in service.start_action_stream(
                student_id=student.id,
                school_id=school_id,
                challenge=challenge,
                action=request.action,
                code=request.code,
                language=request.language,
                error=request.error,
                test_results=request.test_results,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Coding AI streaming error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': 'Internal server error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Follow-up Message (streaming)
# ---------------------------------------------------------------------------

@router.post(
    "/sessions/{session_id}/messages/stream",
    summary="Send follow-up message in coding chat",
)
async def send_coding_message(
    session_id: int,
    request: CodingChatMessageRequest,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Send a follow-up message in an existing coding AI chat session."""
    service = CodingChatService(db)

    async def event_generator():
        try:
            async for event in service.send_followup_stream(
                session_id=session_id,
                student_id=student.id,
                school_id=school_id,
                content=request.content,
                code=request.code,
                error=request.error,
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except Exception as e:
            logger.error(f"Coding AI follow-up error: {e}")
            yield f"data: {json.dumps({'type': 'error', 'error': 'Internal server error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# ---------------------------------------------------------------------------
# Get Session
# ---------------------------------------------------------------------------

@router.get("/sessions/{session_id}", summary="Get coding chat session with messages")
async def get_coding_session(
    session_id: int,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a coding AI chat session with full message history."""
    service = CodingChatService(db)

    session = await service.get_session_with_messages(session_id, student.id, school_id)
    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found",
        )

    from app.services.coding_chat_service import _message_to_dict, _session_to_dict

    return {
        **_session_to_dict(session),
        "messages": [_message_to_dict(m) for m in session.messages if not m.is_deleted],
    }


# ---------------------------------------------------------------------------
# Find Active Session for Challenge
# ---------------------------------------------------------------------------

@router.get(
    "/challenge/{challenge_id}/session",
    summary="Find active coding chat session for a challenge",
)
async def get_challenge_session(
    challenge_id: int,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get the active coding chat session for a specific challenge (if exists)."""
    service = CodingChatService(db)

    session = await service.get_challenge_session(challenge_id, student.id, school_id)
    if not session:
        return None

    from app.services.coding_chat_service import _message_to_dict, _session_to_dict

    return {
        **_session_to_dict(session),
        "messages": [_message_to_dict(m) for m in session.messages if not m.is_deleted],
    }
