"""
Teacher API endpoints for browsing textbook exercises.

Used when creating homework — teacher can pick specific exercises.
All endpoints require TEACHER role.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import require_teacher, get_current_user_school_id
from app.repositories.exercise_repo import ExerciseRepository
from app.schemas.exercise import (
    ExerciseWithAnswerResponse,
    ExerciseListWithAnswersResponse,
)

router = APIRouter()


@router.get(
    "/teachers/exercises",
    response_model=ExerciseListWithAnswersResponse,
    summary="List exercises for a paragraph (with answers)",
)
async def list_exercises_for_teacher(
    paragraph_id: int = Query(..., description="Paragraph ID"),
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: A, B, or C"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get exercises for a paragraph WITH answers. For homework creation."""
    repo = ExerciseRepository(db)
    exercises = await repo.list_by_paragraph(
        paragraph_id=paragraph_id,
        difficulty=difficulty,
        school_id=school_id,
    )
    counts = await repo.count_by_difficulty(paragraph_id)

    return ExerciseListWithAnswersResponse(
        paragraph_id=paragraph_id,
        total=len(exercises),
        count_a=counts.get("A", 0),
        count_b=counts.get("B", 0),
        count_c=counts.get("C", 0),
        exercises=[ExerciseWithAnswerResponse.model_validate(e) for e in exercises],
    )
