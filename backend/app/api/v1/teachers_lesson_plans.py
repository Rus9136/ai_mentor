"""
Teacher Lesson Plan API endpoints.

Endpoints for generating AI-powered lesson plans (QMJ).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_school_id, get_teacher_from_user
from app.core.database import get_db
from app.models.teacher import Teacher
from app.schemas.lesson_plan import (
    LessonPlanGenerateRequest,
    LessonPlanGenerateResponse,
)
from app.services.lesson_plan_service import LessonPlanService
from app.services.llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/lesson-plans", tags=["teachers-lesson-plans"])


@router.post(
    "/generate",
    response_model=LessonPlanGenerateResponse,
    summary="Generate lesson plan (QMJ)",
)
async def generate_lesson_plan(
    request: LessonPlanGenerateRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI lesson plan (QMJ) for a paragraph."""
    try:
        service = LessonPlanService(db, LLMService())
        return await service.generate(
            paragraph_id=request.paragraph_id,
            school_id=school_id,
            teacher_id=teacher.id,
            class_id=request.class_id,
            language=request.language,
            duration_min=request.duration_min,
        )
    except LLMServiceError:
        logger.exception("LLM service error during lesson plan generation")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="AI service temporarily unavailable",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )
