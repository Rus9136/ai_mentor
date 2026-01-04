"""
School Question Option Management API for ADMIN.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.test import QuestionOption
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.repositories.test_repo import TestRepository
from app.schemas.question import (
    QuestionOptionCreate,
    QuestionOptionUpdate,
    QuestionOptionResponse,
)
from ._dependencies import require_school_question, require_school_option


router = APIRouter(tags=["School Question Options"])


@router.post("/questions/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_school_question_option(
    question_id: int,
    data: QuestionOptionCreate,
    question_and_test=Depends(require_school_question),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new option for a question in a school test (ADMIN only).
    Cannot add options to questions in global tests.
    """
    question, test = question_and_test
    option_repo = QuestionOptionRepository(db)

    # Create option
    option = QuestionOption(question_id=question_id, **data.model_dump())
    return await option_repo.create(option)


@router.put("/options/{option_id}")
async def update_school_question_option(
    data: QuestionOptionUpdate,
    option_hierarchy=Depends(require_school_option),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question option in a school test (ADMIN only).
    Cannot update options in global tests.
    """
    option, question, test = option_hierarchy
    option_repo = QuestionOptionRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)

    updated_option = await option_repo.update(option)

    # Return as dict
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
async def delete_school_question_option(
    option_hierarchy=Depends(require_school_option),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question option in a school test (ADMIN only).
    Cannot delete options in global tests.
    """
    option, question, test = option_hierarchy
    option_repo = QuestionOptionRepository(db)
    await option_repo.soft_delete(option)
