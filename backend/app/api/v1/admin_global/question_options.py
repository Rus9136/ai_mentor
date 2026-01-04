"""
Global QuestionOption CRUD endpoints for SUPER_ADMIN.
Manages question options in global tests (school_id = NULL).
"""

from typing import Tuple
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.test import Test, Question, QuestionOption
from app.repositories.question_repo import QuestionOptionRepository
from app.schemas.question import (
    QuestionOptionCreate,
    QuestionOptionUpdate,
    QuestionOptionResponse,
)
from ._dependencies import require_global_question, require_global_option


router = APIRouter()


@router.post("/questions/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_global_question_option(
    data: QuestionOptionCreate,
    question_and_test: Tuple[Question, Test] = Depends(require_global_question),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new option for a question in a global test (SUPER_ADMIN only).
    """
    question, _ = question_and_test
    option_repo = QuestionOptionRepository(db)

    # Create option
    option = QuestionOption(question_id=question.id, **data.model_dump())
    return await option_repo.create(option)


@router.put("/options/{option_id}")
async def update_global_question_option(
    data: QuestionOptionUpdate,
    option_data: Tuple[QuestionOption, Question, Test] = Depends(require_global_option),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question option in a global test (SUPER_ADMIN only).
    Returns option as dict to avoid SQLAlchemy lazy loading issues.
    """
    option, _, _ = option_data
    option_repo = QuestionOptionRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)

    updated_option = await option_repo.update(option)

    # Return option as simple dict (avoid SQLAlchemy lazy loading issues)
    return {
        "id": updated_option.id,
        "question_id": updated_option.question_id,
        "sort_order": updated_option.sort_order,
        "option_text": updated_option.option_text,
        "is_correct": updated_option.is_correct,
        "created_at": updated_option.created_at.isoformat() if updated_option.created_at else None,
        "updated_at": updated_option.updated_at.isoformat() if updated_option.updated_at else None,
        "deleted_at": updated_option.deleted_at.isoformat() if updated_option.deleted_at else None,
        "is_deleted": updated_option.is_deleted,
    }


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_question_option(
    option_data: Tuple[QuestionOption, Question, Test] = Depends(require_global_option),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question option in a global test (SUPER_ADMIN only).
    """
    option, _, _ = option_data
    option_repo = QuestionOptionRepository(db)
    await option_repo.soft_delete(option)
