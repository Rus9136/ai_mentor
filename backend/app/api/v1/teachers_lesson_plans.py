"""
Teacher Lesson Plan API endpoints.

Endpoints for generating, saving, listing, and exporting AI-powered lesson plans (QMJ).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_school_id, get_teacher_from_user
from app.core.database import get_db
from app.models.teacher import Teacher
from app.schemas.lesson_plan import (
    LessonPlanFullResponse,
    LessonPlanGenerateRequest,
    LessonPlanGenerateResponse,
    LessonPlanListItem,
    LessonPlanSaveRequest,
    LessonPlanUpdateRequest,
)
from app.services.lesson_plan_export import export_to_docx
from app.services.lesson_plan_service import LessonPlanService
from app.services.llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/lesson-plans", tags=["teachers-lesson-plans"])


def _get_service(db: AsyncSession) -> LessonPlanService:
    return LessonPlanService(db, LLMService())


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
        service = _get_service(db)
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


@router.post(
    "",
    response_model=LessonPlanFullResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save lesson plan",
)
async def save_lesson_plan(
    data: LessonPlanSaveRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Save a generated lesson plan to the database."""
    service = _get_service(db)
    plan = await service.save(teacher_id=teacher.id, school_id=school_id, data=data)
    return _build_full_response(plan)


@router.get(
    "",
    response_model=list[LessonPlanListItem],
    summary="List saved lesson plans",
)
async def list_lesson_plans(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """List teacher's saved lesson plans."""
    service = _get_service(db)
    plans = await service.list_by_teacher(
        teacher_id=teacher.id,
        school_id=school_id,
        skip=skip,
        limit=limit,
    )
    return [_build_list_item(p) for p in plans]


@router.get(
    "/{plan_id}",
    response_model=LessonPlanFullResponse,
    summary="Get lesson plan by ID",
)
async def get_lesson_plan(
    plan_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single lesson plan."""
    service = _get_service(db)
    plan = await service.get_by_id(plan_id, teacher.id, school_id)
    return _build_full_response(plan)


@router.put(
    "/{plan_id}",
    response_model=LessonPlanFullResponse,
    summary="Update lesson plan",
)
async def update_lesson_plan(
    plan_id: int,
    data: LessonPlanUpdateRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a lesson plan (title or plan data)."""
    service = _get_service(db)
    plan = await service.update(plan_id, teacher.id, school_id, data)
    return _build_full_response(plan)


@router.delete(
    "/{plan_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete lesson plan",
)
async def delete_lesson_plan(
    plan_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a lesson plan."""
    service = _get_service(db)
    await service.delete(plan_id, teacher.id, school_id)


@router.get(
    "/{plan_id}/export/docx",
    summary="Export lesson plan as DOCX",
)
async def export_lesson_plan_docx(
    plan_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Download lesson plan as DOCX file."""
    service = _get_service(db)
    plan = await service.get_by_id(plan_id, teacher.id, school_id)
    buf = export_to_docx(plan.plan_data, plan.context_data)
    from urllib.parse import quote
    safe_name = f"QMJ_{plan.id}.docx"
    utf8_name = f"QMJ_{plan.title[:50].replace(' ', '_')}.docx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{quote(utf8_name)}"
        },
    )


def _build_full_response(plan) -> LessonPlanFullResponse:
    return LessonPlanFullResponse(
        id=plan.id,
        title=plan.title,
        teacher_id=plan.teacher_id,
        school_id=plan.school_id,
        paragraph_id=plan.paragraph_id,
        class_id=plan.class_id,
        language=plan.language,
        duration_min=plan.duration_min,
        plan_data=plan.plan_data,
        context_data=plan.context_data,
        created_at=plan.created_at,
        updated_at=plan.updated_at,
    )


def _build_list_item(plan) -> LessonPlanListItem:
    ctx = plan.context_data or {}
    return LessonPlanListItem(
        id=plan.id,
        title=plan.title,
        language=plan.language,
        duration_min=plan.duration_min,
        paragraph_id=plan.paragraph_id,
        class_id=plan.class_id,
        subject=ctx.get("subject"),
        grade_level=ctx.get("grade_level"),
        created_at=plan.created_at,
    )
