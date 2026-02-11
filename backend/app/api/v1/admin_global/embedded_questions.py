"""
Global Embedded Question CRUD endpoints for SUPER_ADMIN.
Manages embedded questions ("Проверь себя") in global paragraphs (school_id = NULL).
"""

from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.models.textbook import Textbook
from app.models.embedded_question import EmbeddedQuestion
from app.repositories.embedded_question_repo import EmbeddedQuestionRepository
from app.schemas.embedded_question import (
    EmbeddedQuestionCreate,
    EmbeddedQuestionUpdate,
    EmbeddedQuestionResponse,
)
from ._dependencies import require_global_paragraph, require_global_embedded_question


router = APIRouter(tags=["Global Embedded Questions"])


@router.post(
    "/paragraphs/{paragraph_id}/embedded-questions",
    response_model=EmbeddedQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_global_embedded_question(
    data: EmbeddedQuestionCreate,
    paragraph_tuple: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create an embedded question in a global paragraph (SUPER_ADMIN only)."""
    paragraph, _, _ = paragraph_tuple
    repo = EmbeddedQuestionRepository(db)

    question_data = data.model_dump(exclude={"paragraph_id"})
    # Convert options from Pydantic models to dicts for JSONB storage
    if question_data.get("options"):
        question_data["options"] = [
            opt.model_dump() if hasattr(opt, "model_dump") else opt
            for opt in data.options
        ]

    question = EmbeddedQuestion(paragraph_id=paragraph.id, **question_data)
    created = await repo.create(question)
    return created


@router.get(
    "/paragraphs/{paragraph_id}/embedded-questions",
    response_model=List[EmbeddedQuestionResponse],
)
async def list_global_embedded_questions(
    paragraph_tuple: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all embedded questions for a global paragraph (SUPER_ADMIN only)."""
    paragraph, _, _ = paragraph_tuple
    repo = EmbeddedQuestionRepository(db)
    questions = await repo.get_by_paragraph(paragraph.id)
    return questions


@router.get(
    "/embedded-questions/{embedded_question_id}",
    response_model=EmbeddedQuestionResponse,
)
async def get_global_embedded_question(
    eq_tuple: Tuple[EmbeddedQuestion, Paragraph, Chapter, Textbook] = Depends(
        require_global_embedded_question
    ),
    current_user: User = Depends(require_super_admin),
):
    """Get a specific embedded question by ID (SUPER_ADMIN only)."""
    question, _, _, _ = eq_tuple
    return question


@router.put(
    "/embedded-questions/{embedded_question_id}",
    response_model=EmbeddedQuestionResponse,
)
async def update_global_embedded_question(
    data: EmbeddedQuestionUpdate,
    eq_tuple: Tuple[EmbeddedQuestion, Paragraph, Chapter, Textbook] = Depends(
        require_global_embedded_question
    ),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an embedded question in a global paragraph (SUPER_ADMIN only)."""
    question, _, _, _ = eq_tuple
    repo = EmbeddedQuestionRepository(db)

    update_data = data.model_dump(exclude_unset=True)
    # Convert options from Pydantic models to dicts for JSONB storage
    if "options" in update_data and update_data["options"] is not None:
        update_data["options"] = [
            opt.model_dump() if hasattr(opt, "model_dump") else opt
            for opt in data.options
        ]

    for field, value in update_data.items():
        setattr(question, field, value)

    updated = await repo.update(question)
    return updated


@router.delete(
    "/embedded-questions/{embedded_question_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_global_embedded_question(
    eq_tuple: Tuple[EmbeddedQuestion, Paragraph, Chapter, Textbook] = Depends(
        require_global_embedded_question
    ),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete an embedded question in a global paragraph (SUPER_ADMIN only)."""
    question, _, _, _ = eq_tuple
    repo = EmbeddedQuestionRepository(db)
    await repo.soft_delete(question)
