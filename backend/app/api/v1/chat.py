"""
Chat API endpoints for RAG-based conversations.
"""
import json
import logging
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    require_super_admin,
    get_current_user_school_id,
)
from app.models.user import User
from app.models.student import Student
from app.services.chat_service import ChatService
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    ChatSessionDetailResponse,
    ChatMessageCreate,
    ChatMessageResponse,
    ChatResponse,
    SystemPromptCreate,
    SystemPromptUpdate,
    SystemPromptResponse,
)
from app.schemas.rag import Citation

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# Helper Functions
# =============================================================================

async def get_student_from_user(db: AsyncSession, user: User) -> Student:
    """Get Student record from User."""
    result = await db.execute(
        select(Student).where(Student.user_id == user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student record not found for this user"
        )
    return student


# =============================================================================
# Student Chat Endpoints
# =============================================================================

@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_chat_session(
    request: ChatSessionCreate,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chat session.

    - **session_type**: Type of chat (reading_help, post_paragraph, test_help, general_tutor)
    - **paragraph_id**: Optional paragraph context
    - **chapter_id**: Optional chapter context
    - **test_id**: Optional test context
    - **language**: Response language (ru/kk)
    """
    student = await get_student_from_user(db, current_user)

    chat_service = ChatService(db)
    session = await chat_service.create_session(
        student_id=student.id,
        school_id=school_id,
        session_type=request.session_type,
        paragraph_id=request.paragraph_id,
        chapter_id=request.chapter_id,
        test_id=request.test_id,
        title=request.title,
        language=request.language
    )

    return chat_service._session_to_response(session)


@router.get("/sessions", response_model=ChatSessionListResponse)
async def list_chat_sessions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    session_type: Optional[str] = Query(None),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    List student's chat sessions with pagination.

    - **page**: Page number (1-indexed)
    - **page_size**: Items per page (max 100)
    - **session_type**: Optional filter by session type
    """
    student = await get_student_from_user(db, current_user)

    chat_service = ChatService(db)
    sessions, total = await chat_service.list_sessions(
        student_id=student.id,
        school_id=school_id,
        session_type=session_type,
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
async def get_chat_session(
    session_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chat session with full message history.
    """
    student = await get_student_from_user(db, current_user)

    chat_service = ChatService(db)
    session = await chat_service.get_session_with_messages(
        session_id=session_id,
        student_id=student.id,
        school_id=school_id
    )

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found"
        )

    # Convert messages with citations parsing
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
        created_at=session.created_at,
        messages=messages
    )


@router.post("/sessions/{session_id}/messages", response_model=ChatResponse)
async def send_message(
    session_id: int,
    request: ChatMessageCreate,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Send a message and get AI response.

    Uses RAG to retrieve relevant context and generates response
    based on student's mastery level (A/B/C).
    """
    student = await get_student_from_user(db, current_user)

    chat_service = ChatService(db)

    try:
        response = await chat_service.send_message(
            session_id=session_id,
            student_id=student.id,
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
        logger.error(f"Error in chat: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process message: {str(e)}"
        )


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_chat_session(
    session_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a chat session.
    """
    student = await get_student_from_user(db, current_user)

    chat_service = ChatService(db)
    success = await chat_service.delete_session(
        session_id=session_id,
        student_id=student.id,
        school_id=school_id
    )

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chat session {session_id} not found"
        )


# =============================================================================
# Admin Endpoints (System Prompts)
# =============================================================================

@router.get("/admin/prompts", response_model=List[SystemPromptResponse])
async def list_system_prompts(
    prompt_type: Optional[str] = Query(None),
    mastery_level: Optional[str] = Query(None),
    language: Optional[str] = Query(None),
    include_inactive: bool = Query(False),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    List all system prompt templates (SUPER_ADMIN only).
    """
    chat_service = ChatService(db)
    prompts = await chat_service.list_prompts(
        prompt_type=prompt_type,
        mastery_level=mastery_level,
        language=language,
        include_inactive=include_inactive
    )
    return prompts


@router.post(
    "/admin/prompts",
    response_model=SystemPromptResponse,
    status_code=status.HTTP_201_CREATED
)
async def create_system_prompt(
    request: SystemPromptCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new system prompt template (SUPER_ADMIN only).
    """
    chat_service = ChatService(db)
    prompt = await chat_service.create_prompt(request)
    return prompt


@router.get("/admin/prompts/{prompt_id}", response_model=SystemPromptResponse)
async def get_system_prompt(
    prompt_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a system prompt template by ID (SUPER_ADMIN only).
    """
    chat_service = ChatService(db)
    prompt = await chat_service.get_prompt_by_id(prompt_id)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System prompt {prompt_id} not found"
        )

    return prompt


@router.put("/admin/prompts/{prompt_id}", response_model=SystemPromptResponse)
async def update_system_prompt(
    prompt_id: int,
    request: SystemPromptUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a system prompt template (SUPER_ADMIN only).

    Increments version number on each update.
    """
    chat_service = ChatService(db)
    prompt = await chat_service.update_prompt(prompt_id, request)

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System prompt {prompt_id} not found"
        )

    return prompt


@router.delete("/admin/prompts/{prompt_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_system_prompt(
    prompt_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a system prompt template (SUPER_ADMIN only).
    """
    chat_service = ChatService(db)
    success = await chat_service.delete_prompt(prompt_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System prompt {prompt_id} not found"
        )
