"""
Teacher Chat API endpoints for RAG-based conversations.

Teachers can chat with AI about textbook content to prepare lessons,
understand material, generate explanations, etc.
"""
import json
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    get_teacher_from_user,
    get_current_user_school_id,
)
from app.models.teacher import Teacher
from app.services.chat_service import ChatService
from app.schemas.chat import (
    TeacherChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatSessionDetailResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponse,
)
from app.schemas.rag import Citation

router = APIRouter()
logger = logging.getLogger(__name__)


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_teacher_chat_session(
    request: TeacherChatSessionCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Create a new teacher chat session with paragraph context."""
    chat_service = ChatService(db)
    session = await chat_service.create_teacher_session(
        teacher_id=teacher.id,
        school_id=school_id,
        paragraph_id=request.paragraph_id,
        chapter_id=request.chapter_id,
        title=request.title,
        language=request.language
    )
    return chat_service._session_to_response(session)


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_teacher_chat_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """List teacher's chat sessions with pagination."""
    chat_service = ChatService(db)
    sessions, total = await chat_service.list_teacher_sessions(
        teacher_id=teacher.id,
        school_id=school_id,
        page=page,
        page_size=page_size
    )
    return ChatSessionListResponse(
        items=[chat_service._session_to_response(s) for s in sessions],
        total=total,
        page=page,
        page_size=page_size
    )


@router.get("/sessions/{session_id}", response_model=ChatSessionDetailResponse)
async def get_teacher_chat_session(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Get teacher chat session with full message history."""
    chat_service = ChatService(db)
    session = await chat_service.get_teacher_session_with_messages(
        session_id=session_id,
        teacher_id=teacher.id,
        school_id=school_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found"
        )

    messages = []
    for msg in session.messages:
        if not msg.is_deleted:
            citations = None
            if msg.citations_json:
                try:
                    citations_data = json.loads(msg.citations_json)
                    citations = [Citation(**c) for c in citations_data]
                except (json.JSONDecodeError, TypeError):
                    citations = None

            messages.append(ChatMessageResponse(
                id=msg.id,
                role=msg.role,
                content=msg.content,
                citations=citations,
                tokens_used=msg.tokens_used,
                model_used=msg.model_used,
                processing_time_ms=msg.processing_time_ms,
                created_at=msg.created_at
            ))

    return ChatSessionDetailResponse(
        id=session.id,
        session_type=session.session_type,
        paragraph_id=session.paragraph_id,
        chapter_id=session.chapter_id,
        test_id=session.test_id,
        title=session.title,
        mastery_level=session.mastery_level,
        language=session.language,
        message_count=session.message_count,
        total_tokens_used=session.total_tokens_used,
        last_message_at=session.last_message_at,
        created_at=session.created_at,
        teacher_id=session.teacher_id,
        messages=messages
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_teacher_message(
    session_id: int,
    request: ChatMessageCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and get AI response with textbook context."""
    chat_service = ChatService(db)
    try:
        response = await chat_service.send_teacher_message(
            session_id=session_id,
            teacher_id=teacher.id,
            school_id=school_id,
            content=request.content
        )
        return response
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Error in teacher chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.post("/sessions/{session_id}/messages/stream")
async def send_teacher_message_stream(
    session_id: int,
    request: ChatMessageCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Send a message and stream AI response via Server-Sent Events."""
    chat_service = ChatService(db)

    async def event_generator():
        try:
            async for event in chat_service.send_teacher_message_stream(
                session_id=session_id,
                teacher_id=teacher.id,
                school_id=school_id,
                content=request.content,
                model=request.model
            ):
                yield f"data: {json.dumps(event)}\n\n"
        except ValueError as e:
            yield f"data: {json.dumps({'type': 'error', 'error': str(e)})}\n\n"
        except Exception as e:
            logger.error(f"Teacher chat streaming error: {str(e)}")
            yield f"data: {json.dumps({'type': 'error', 'error': 'Internal server error'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher_chat_session(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """Soft delete a teacher chat session."""
    chat_service = ChatService(db)
    success = await chat_service.delete_teacher_session(
        session_id=session_id,
        teacher_id=teacher.id,
        school_id=school_id
    )
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found"
        )
