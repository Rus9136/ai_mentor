"""
Student API endpoints for browsing textbook exercises.

Exercises are shown WITHOUT answers.
"""
from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_student_from_user, get_current_user_school_id
from app.models.student import Student
from app.repositories.exercise_repo import ExerciseRepository
from app.schemas.exercise import ExerciseResponse, ExerciseListResponse

router = APIRouter()


@router.get(
    "/paragraphs/{paragraph_id}/exercises",
    response_model=ExerciseListResponse,
    summary="List exercises for a paragraph (without answers)",
)
async def list_exercises_for_student(
    paragraph_id: int,
    difficulty: Optional[str] = Query(None, description="Filter by difficulty: A, B, or C"),
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get exercises for a paragraph WITHOUT answers."""
    repo = ExerciseRepository(db)
    exercises = await repo.list_by_paragraph(
        paragraph_id=paragraph_id,
        difficulty=difficulty,
        school_id=school_id,
    )
    counts = await repo.count_by_difficulty(paragraph_id)

    return ExerciseListResponse(
        paragraph_id=paragraph_id,
        total=len(exercises),
        count_a=counts.get("A", 0),
        count_b=counts.get("B", 0),
        count_c=counts.get("C", 0),
        exercises=[ExerciseResponse.model_validate(e) for e in exercises],
    )
