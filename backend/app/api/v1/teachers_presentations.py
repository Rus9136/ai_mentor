"""
Teacher Presentation API endpoints.

Endpoints for generating, saving, listing, and exporting AI-powered PPTX presentations.
"""
import asyncio
import logging
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_school_id, get_teacher_from_user
from app.core.database import get_db
from app.models.teacher import Teacher
from app.schemas.presentation import (
    PresentationFullResponse,
    PresentationGenerateRequest,
    PresentationGenerateResponse,
    PresentationListItem,
    PresentationSaveRequest,
    PresentationUpdateRequest,
    UpdatePresentationThemeRequest,
    UpdatePresentationThemeResponse,
)
from app.core.config import settings
from app.services.presentation_export import export_to_pptx as export_to_pptx_v1
from app.services.presentation_export import get_available_templates as get_available_templates_v1
from app.services.presentation_export_v2 import export_to_pptx as export_to_pptx_v2
from app.services.presentation_export_v2 import get_available_templates as get_available_templates_v2
from app.services.presentation_service import PresentationService
from app.services.llm_service import LLMService, LLMServiceError


def _get_exporter():
    """Select exporter based on PRESENTATION_EXPORTER_VERSION env var."""
    if settings.PRESENTATION_EXPORTER_VERSION == "v2":
        return export_to_pptx_v2, get_available_templates_v2
    return export_to_pptx_v1, get_available_templates_v1

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/presentations", tags=["teachers-presentations"])


def _get_service(db: AsyncSession) -> PresentationService:
    return PresentationService(db, LLMService())


@router.post(
    "/generate",
    response_model=PresentationGenerateResponse,
    summary="Generate presentation from paragraph",
)
async def generate_presentation(
    request: PresentationGenerateRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Generate AI presentation slides for a paragraph."""
    service = _get_service(db)
    await service.check_rate_limit(teacher.user_id)
    try:
        return await service.generate(
            paragraph_id=request.paragraph_id,
            school_id=school_id,
            teacher_id=teacher.id,
            user_id=teacher.user_id,
            class_id=request.class_id,
            language=request.language,
            slide_count=request.slide_count,
            theme=request.theme,
        )
    except LLMServiceError:
        logger.exception("LLM service error during presentation generation")
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
    response_model=PresentationFullResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Save presentation",
)
async def save_presentation(
    data: PresentationSaveRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Save a generated presentation to the database."""
    service = _get_service(db)
    pres = await service.save(teacher_id=teacher.id, school_id=school_id, data=data)
    return _build_full_response(pres)


@router.get(
    "",
    response_model=list[PresentationListItem],
    summary="List saved presentations",
)
async def list_presentations(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """List teacher's saved presentations."""
    service = _get_service(db)
    presentations = await service.list_by_teacher(
        teacher_id=teacher.id,
        school_id=school_id,
        skip=skip,
        limit=limit,
    )
    return [_build_list_item(p) for p in presentations]


@router.get(
    "/templates",
    summary="List available PPTX templates",
)
async def list_templates(
    teacher: Teacher = Depends(get_teacher_from_user),
):
    """Get list of available presentation templates."""
    _, get_templates_fn = _get_exporter()
    return get_templates_fn()


@router.patch(
    "/{presentation_id}/theme",
    response_model=UpdatePresentationThemeResponse,
    summary="Change presentation theme",
)
async def update_presentation_theme(
    presentation_id: int,
    data: UpdatePresentationThemeRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Change presentation theme without regenerating content."""
    service = _get_service(db)
    pres = await service.update_theme(presentation_id, teacher.id, school_id, data.theme)
    return UpdatePresentationThemeResponse(
        id=pres.id,
        context_data=pres.context_data,
        updated_at=pres.updated_at,
    )


@router.get(
    "/{presentation_id}",
    response_model=PresentationFullResponse,
    summary="Get presentation by ID",
)
async def get_presentation(
    presentation_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get a single presentation."""
    service = _get_service(db)
    pres = await service.get_by_id(presentation_id, teacher.id, school_id)
    return _build_full_response(pres)


@router.put(
    "/{presentation_id}",
    response_model=PresentationFullResponse,
    summary="Update presentation",
)
async def update_presentation(
    presentation_id: int,
    data: PresentationUpdateRequest,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a presentation (title or slides data)."""
    service = _get_service(db)
    pres = await service.update(presentation_id, teacher.id, school_id, data)
    return _build_full_response(pres)


@router.delete(
    "/{presentation_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete presentation",
)
async def delete_presentation(
    presentation_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Delete a presentation."""
    service = _get_service(db)
    await service.delete(presentation_id, teacher.id, school_id)


@router.get(
    "/{presentation_id}/export/pptx",
    summary="Export presentation as PPTX",
)
async def export_presentation_pptx(
    presentation_id: int,
    template: str = Query("academic", description="Template slug"),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Download presentation as PPTX file."""
    service = _get_service(db)
    pres = await service.get_by_id(presentation_id, teacher.id, school_id)
    export_fn, _ = _get_exporter()
    # Inject language into context for v2 exporter localization
    export_context = {**(pres.context_data or {}), "language": pres.language}
    loop = asyncio.get_event_loop()
    buf = await loop.run_in_executor(
        None, lambda: export_fn(pres.slides_data, export_context, template=template)
    )
    safe_name = f"Presentation_{pres.id}.pptx"
    utf8_name = f"Presentation_{pres.title[:50].replace(' ', '_')}.pptx"
    return StreamingResponse(
        buf,
        media_type="application/vnd.openxmlformats-officedocument.presentationml.presentation",
        headers={
            "Content-Disposition": f"attachment; filename=\"{safe_name}\"; filename*=UTF-8''{quote(utf8_name)}"
        },
    )


def _build_full_response(pres) -> PresentationFullResponse:
    return PresentationFullResponse(
        id=pres.id,
        title=pres.title,
        teacher_id=pres.teacher_id,
        school_id=pres.school_id,
        paragraph_id=pres.paragraph_id,
        class_id=pres.class_id,
        language=pres.language,
        slide_count=pres.slide_count,
        slides_data=pres.slides_data,
        context_data=pres.context_data,
        created_at=pres.created_at,
        updated_at=pres.updated_at,
    )


def _build_list_item(pres) -> PresentationListItem:
    ctx = pres.context_data or {}
    return PresentationListItem(
        id=pres.id,
        title=pres.title,
        language=pres.language,
        slide_count=pres.slide_count,
        paragraph_id=pres.paragraph_id,
        class_id=pres.class_id,
        subject=ctx.get("subject"),
        grade_level=ctx.get("grade_level"),
        created_at=pres.created_at,
    )
