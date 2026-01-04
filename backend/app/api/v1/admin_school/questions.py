"""
School Question Management API for ADMIN.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.test import Question, QuestionOption
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
)
from ._dependencies import (
    get_test_for_school_admin,
    require_school_test,
    get_question_for_school_admin,
    require_school_question,
)


router = APIRouter(tags=["School Questions"])


@router.post("/tests/{test_id}/questions", status_code=status.HTTP_201_CREATED)
async def create_school_question(
    test_id: int,
    data: QuestionCreate,
    test=Depends(require_school_test),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new question in a school test (ADMIN only).
    Cannot add questions to global tests.
    Supports creating question with nested options in a single request.
    """
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    # Extract options from data
    options_data = data.options
    question_data = data.model_dump(exclude={'options'})

    # Create question
    question = Question(test_id=test_id, **question_data)
    created_question = await question_repo.create(question)

    # Create options if provided
    created_options = []
    if options_data:
        for option_create in options_data:
            option = QuestionOption(
                question_id=created_question.id,
                **option_create.model_dump()
            )
            created_option = await option_repo.create(option)
            created_options.append(created_option)

    # Return question details as dict (avoid SQLAlchemy lazy loading)
    return {
        "id": created_question.id,
        "test_id": created_question.test_id,
        "sort_order": created_question.sort_order,
        "question_type": created_question.question_type.value if hasattr(created_question.question_type, 'value') else created_question.question_type,
        "question_text": created_question.question_text,
        "explanation": created_question.explanation,
        "points": created_question.points,
        "created_at": created_question.created_at.isoformat() if created_question.created_at else None,
        "updated_at": created_question.updated_at.isoformat() if created_question.updated_at else None,
        "deleted_at": created_question.deleted_at.isoformat() if created_question.deleted_at else None,
        "is_deleted": created_question.is_deleted,
        "options": [
            {
                "id": opt.id,
                "question_id": opt.question_id,
                "sort_order": opt.sort_order,
                "option_text": opt.option_text,
                "is_correct": opt.is_correct,
                "created_at": opt.created_at.isoformat() if opt.created_at else None,
                "updated_at": opt.updated_at.isoformat() if opt.updated_at else None,
                "deleted_at": opt.deleted_at.isoformat() if opt.deleted_at else None,
                "is_deleted": opt.is_deleted,
            }
            for opt in created_options
        ]
    }


@router.get("/tests/{test_id}/questions", response_model=List[QuestionResponse])
async def list_school_questions(
    test_id: int,
    test=Depends(get_test_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all questions for a test (ADMIN only).
    Can access questions from global and own school tests.
    """
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    # Get questions WITHOUT eager loading options (avoid RLS issues)
    questions = await question_repo.get_by_test(test_id, load_options=False)

    # Manually load options and build response
    result = []
    for question in questions:
        options = await option_repo.get_by_question(question.id)

        q_dict = {
            "id": question.id,
            "test_id": question.test_id,
            "sort_order": question.sort_order,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "explanation": question.explanation,
            "points": question.points,
            "created_at": question.created_at,
            "updated_at": question.updated_at,
            "deleted_at": question.deleted_at,
            "is_deleted": question.is_deleted,
            "options": [
                {
                    "id": opt.id,
                    "question_id": opt.question_id,
                    "sort_order": opt.sort_order,
                    "option_text": opt.option_text,
                    "is_correct": opt.is_correct,
                    "created_at": opt.created_at,
                    "updated_at": opt.updated_at,
                    "deleted_at": opt.deleted_at,
                    "is_deleted": opt.is_deleted,
                }
                for opt in options
            ]
        }
        q_response = QuestionResponse(**q_dict)
        result.append(q_response)

    return result


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_school_question(
    question: Question = Depends(get_question_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific question by ID (ADMIN only).
    Can access questions from global and own school tests.
    """
    return question


@router.put("/questions/{question_id}")
async def update_school_question(
    data: QuestionUpdate,
    question_and_test=Depends(require_school_question),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question in a school test (ADMIN only).
    Cannot update questions in global tests.
    """
    question, test = question_and_test
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    updated_question = await question_repo.update(question)

    # Manually load options
    options = await option_repo.get_by_question(updated_question.id)

    # Return as dict
    return {
        "id": updated_question.id,
        "test_id": updated_question.test_id,
        "sort_order": updated_question.sort_order,
        "question_type": updated_question.question_type.value if hasattr(updated_question.question_type, 'value') else updated_question.question_type,
        "question_text": updated_question.question_text,
        "explanation": updated_question.explanation,
        "points": updated_question.points,
        "created_at": updated_question.created_at.isoformat() if updated_question.created_at else None,
        "updated_at": updated_question.updated_at.isoformat() if updated_question.updated_at else None,
        "deleted_at": updated_question.deleted_at.isoformat() if updated_question.deleted_at else None,
        "is_deleted": updated_question.is_deleted,
        "options": [
            {
                "id": opt.id,
                "question_id": opt.question_id,
                "sort_order": opt.sort_order,
                "option_text": opt.option_text,
                "is_correct": opt.is_correct,
                "created_at": opt.created_at.isoformat() if opt.created_at else None,
                "updated_at": opt.updated_at.isoformat() if opt.updated_at else None,
                "deleted_at": opt.deleted_at.isoformat() if opt.deleted_at else None,
                "is_deleted": opt.is_deleted,
            }
            for opt in options
        ]
    }


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_question(
    question_and_test=Depends(require_school_question),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question in a school test (ADMIN only).
    Cannot delete questions in global tests.
    """
    question, test = question_and_test
    question_repo = QuestionRepository(db)
    await question_repo.soft_delete(question)
