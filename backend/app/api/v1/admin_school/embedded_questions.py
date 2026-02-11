"""
School Embedded Question CRUD endpoints for ADMIN.
Manages embedded questions ("Проверь себя") in school paragraphs.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.embedded_question import EmbeddedQuestion
from app.repositories.embedded_question_repo import EmbeddedQuestionRepository
from app.schemas.embedded_question import (
    EmbeddedQuestionCreate,
    EmbeddedQuestionUpdate,
    EmbeddedQuestionResponse,
)
from ._dependencies import (
    get_paragraph_for_school_admin,
    require_school_paragraph,
    get_embedded_question_for_school_admin,
    require_school_embedded_question,
)


router = APIRouter(tags=["School Embedded Questions"])


@router.post(
    "/paragraphs/{paragraph_id}/embedded-questions",
    response_model=EmbeddedQuestionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_school_embedded_question(
    paragraph_id: int,
    data: EmbeddedQuestionCreate,
    paragraph_chain=Depends(require_school_paragraph),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create an embedded question in a school paragraph (ADMIN only).
    Cannot add questions to global paragraphs.
    """
    repo = EmbeddedQuestionRepository(db)

    question_data = data.model_dump(exclude={"paragraph_id"})
    # Convert options from Pydantic models to dicts for JSONB storage
    if question_data.get("options"):
        question_data["options"] = [
            opt.model_dump() if hasattr(opt, "model_dump") else opt
            for opt in data.options
        ]

    question = EmbeddedQuestion(paragraph_id=paragraph_id, **question_data)
    created = await repo.create(question)
    return created


@router.get(
    "/paragraphs/{paragraph_id}/embedded-questions",
    response_model=List[EmbeddedQuestionResponse],
)
async def list_school_embedded_questions(
    paragraph_id: int,
    paragraph=Depends(get_paragraph_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all embedded questions for a paragraph (ADMIN only).
    Can access questions from global and own school paragraphs.
    """
    repo = EmbeddedQuestionRepository(db)
    questions = await repo.get_by_paragraph(paragraph_id)
    return questions


@router.get(
    "/embedded-questions/{embedded_question_id}",
    response_model=EmbeddedQuestionResponse,
)
async def get_school_embedded_question(
    question=Depends(get_embedded_question_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific embedded question by ID (ADMIN only).
    Can access questions from global and own school paragraphs.
    """
    return question


@router.put(
    "/embedded-questions/{embedded_question_id}",
    response_model=EmbeddedQuestionResponse,
)
async def update_school_embedded_question(
    data: EmbeddedQuestionUpdate,
    question_chain=Depends(require_school_embedded_question),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an embedded question in a school paragraph (ADMIN only).
    Cannot update questions in global paragraphs.
    """
    question = question_chain[0]
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
async def delete_school_embedded_question(
    question_chain=Depends(require_school_embedded_question),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete an embedded question in a school paragraph (ADMIN only).
    Cannot delete questions in global paragraphs.
    """
    question = question_chain[0]
    repo = EmbeddedQuestionRepository(db)
    await repo.soft_delete(question)
