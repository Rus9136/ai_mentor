"""
API endpoints for ParagraphContent (rich content: explanation, audio, slides, video, cards).

Endpoints are mounted under both:
- /api/v1/admin/global/paragraphs/{paragraph_id}/content - for SUPER_ADMIN (global textbooks)
- /api/v1/admin/school/paragraphs/{paragraph_id}/content - for School ADMIN (school textbooks)
"""
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, File, UploadFile, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.config import settings
from app.models.user import User
from app.api.dependencies import require_super_admin, require_admin, get_current_user
from app.repositories.paragraph_content_repo import ParagraphContentRepository
from app.services.paragraph_content_service import ParagraphContentService
from app.schemas.paragraph_content import (
    ParagraphContentCreate,
    ParagraphContentUpdate,
    ParagraphContentCardsUpdate,
    ParagraphContentResponse,
    ParagraphContentListResponse,
)

# Router for global content (SUPER_ADMIN)
router_global = APIRouter()

# Router for school content (School ADMIN)
router_school = APIRouter()

# Shared service instance
content_service = ParagraphContentService(upload_dir=settings.UPLOAD_DIR)


# ============================================================================
# Helper function to validate paragraph access
# ============================================================================

async def _get_paragraph_or_404(
    db: AsyncSession,
    paragraph_id: int,
    require_global: bool = False,
    school_id: int | None = None
):
    """
    Get paragraph and validate access.

    Args:
        db: Database session
        paragraph_id: Paragraph ID
        require_global: If True, paragraph must be from global textbook (school_id IS NULL)
        school_id: If provided, paragraph must belong to this school

    Returns:
        Paragraph model

    Raises:
        HTTPException: If paragraph not found or access denied
    """
    from sqlalchemy import select
    from sqlalchemy.orm import selectinload
    from app.models.paragraph import Paragraph
    from app.models.chapter import Chapter
    from app.models.textbook import Textbook

    result = await db.execute(
        select(Paragraph)
        .join(Chapter, Chapter.id == Paragraph.chapter_id)
        .join(Textbook, Textbook.id == Chapter.textbook_id)
        .where(
            Paragraph.id == paragraph_id,
            Paragraph.is_deleted == False
        )
        .options(
            selectinload(Paragraph.chapter).selectinload(Chapter.textbook)
        )
    )
    paragraph = result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(status_code=404, detail=f"Paragraph {paragraph_id} not found")

    textbook = paragraph.chapter.textbook

    if require_global:
        if textbook.school_id is not None:
            raise HTTPException(
                status_code=403,
                detail="This endpoint is for global content only. Use school endpoints instead."
            )
    elif school_id is not None:
        if textbook.school_id != school_id:
            raise HTTPException(
                status_code=403,
                detail="Access denied: paragraph belongs to another school"
            )

    return paragraph


# ============================================================================
# GLOBAL CONTENT ENDPOINTS (SUPER_ADMIN)
# ============================================================================

@router_global.get("/{paragraph_id}/content", response_model=ParagraphContentResponse | None)
async def get_global_paragraph_content(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Get rich content for a global paragraph.

    Returns content for specified language, or None if not exists.
    """
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content:
        return None

    return content


@router_global.put("/{paragraph_id}/content", response_model=ParagraphContentResponse)
async def update_global_paragraph_content(
    paragraph_id: int,
    data: ParagraphContentUpdate,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Create or update explanation text for a global paragraph.
    """
    paragraph = await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Update fields
    if data.explain_text is not None:
        content.explain_text = data.explain_text
        content.status_explain = "ready" if data.explain_text else "empty"

    if data.cards is not None:
        content.cards = [card.model_dump() for card in data.cards]
        content.status_cards = "ready" if data.cards else "empty"

    # Update source hash
    content.source_hash = content_service.calculate_source_hash(paragraph)

    await repo.update(content)
    return content


@router_global.put("/{paragraph_id}/content/cards", response_model=ParagraphContentResponse)
async def update_global_paragraph_cards(
    paragraph_id: int,
    data: ParagraphContentCardsUpdate,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Update flashcards for a global paragraph.
    """
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    content.cards = [card.model_dump() for card in data.cards]
    content.status_cards = "ready" if data.cards else "empty"

    await repo.update(content)
    return content


@router_global.post("/{paragraph_id}/content/audio")
async def upload_global_audio(
    paragraph_id: int,
    file: UploadFile = File(...),
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Upload audio file (MP3, OGG, WAV) for a global paragraph.
    Max size: 50 MB
    """
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Delete old file if exists
    if content.audio_url:
        await content_service.delete_media(paragraph_id, language, "audio", content.audio_url)

    # Upload new file
    url = await content_service.upload_media(paragraph_id, language, "audio", file)

    # Update database
    content.audio_url = url
    content.status_audio = "ready"
    await repo.update(content)

    return {"audio_url": url, "status_audio": "ready"}


@router_global.post("/{paragraph_id}/content/slides")
async def upload_global_slides(
    paragraph_id: int,
    file: UploadFile = File(...),
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Upload slides file (PDF, PPTX) for a global paragraph.
    Max size: 50 MB
    """
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Delete old file if exists
    if content.slides_url:
        await content_service.delete_media(paragraph_id, language, "slides", content.slides_url)

    # Upload new file
    url = await content_service.upload_media(paragraph_id, language, "slides", file)

    # Update database
    content.slides_url = url
    content.status_slides = "ready"
    await repo.update(content)

    return {"slides_url": url, "status_slides": "ready"}


@router_global.post("/{paragraph_id}/content/video")
async def upload_global_video(
    paragraph_id: int,
    file: UploadFile = File(...),
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """
    Upload video file (MP4, WEBM) for a global paragraph.
    Max size: 200 MB
    """
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Delete old file if exists
    if content.video_url:
        await content_service.delete_media(paragraph_id, language, "video", content.video_url)

    # Upload new file
    url = await content_service.upload_media(paragraph_id, language, "video", file)

    # Update database
    content.video_url = url
    content.status_video = "ready"
    await repo.update(content)

    return {"video_url": url, "status_video": "ready"}


@router_global.delete("/{paragraph_id}/content/audio")
async def delete_global_audio(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Delete audio file for a global paragraph."""
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content or not content.audio_url:
        raise HTTPException(status_code=404, detail="Audio not found")

    await content_service.delete_media(paragraph_id, language, "audio", content.audio_url)
    await repo.clear_media(content.id, "audio")

    return {"message": "Audio deleted"}


@router_global.delete("/{paragraph_id}/content/slides")
async def delete_global_slides(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Delete slides file for a global paragraph."""
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content or not content.slides_url:
        raise HTTPException(status_code=404, detail="Slides not found")

    await content_service.delete_media(paragraph_id, language, "slides", content.slides_url)
    await repo.clear_media(content.id, "slides")

    return {"message": "Slides deleted"}


@router_global.delete("/{paragraph_id}/content/video")
async def delete_global_video(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_super_admin),
):
    """Delete video file for a global paragraph."""
    await _get_paragraph_or_404(db, paragraph_id, require_global=True)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content or not content.video_url:
        raise HTTPException(status_code=404, detail="Video not found")

    await content_service.delete_media(paragraph_id, language, "video", content.video_url)
    await repo.clear_media(content.id, "video")

    return {"message": "Video deleted"}


# ============================================================================
# SCHOOL CONTENT ENDPOINTS (School ADMIN)
# ============================================================================

@router_school.get("/{paragraph_id}/content", response_model=ParagraphContentResponse | None)
async def get_school_paragraph_content(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Get rich content for a school paragraph.

    Returns content for specified language, or None if not exists.
    """
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content:
        return None

    return content


@router_school.put("/{paragraph_id}/content", response_model=ParagraphContentResponse)
async def update_school_paragraph_content(
    paragraph_id: int,
    data: ParagraphContentUpdate,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Create or update explanation text for a school paragraph.
    """
    paragraph = await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Update fields
    if data.explain_text is not None:
        content.explain_text = data.explain_text
        content.status_explain = "ready" if data.explain_text else "empty"

    if data.cards is not None:
        content.cards = [card.model_dump() for card in data.cards]
        content.status_cards = "ready" if data.cards else "empty"

    # Update source hash
    content.source_hash = content_service.calculate_source_hash(paragraph)

    await repo.update(content)
    return content


@router_school.put("/{paragraph_id}/content/cards", response_model=ParagraphContentResponse)
async def update_school_paragraph_cards(
    paragraph_id: int,
    data: ParagraphContentCardsUpdate,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Update flashcards for a school paragraph.
    """
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    content.cards = [card.model_dump() for card in data.cards]
    content.status_cards = "ready" if data.cards else "empty"

    await repo.update(content)
    return content


@router_school.post("/{paragraph_id}/content/audio")
async def upload_school_audio(
    paragraph_id: int,
    file: UploadFile = File(...),
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Upload audio file (MP3, OGG, WAV) for a school paragraph.
    Max size: 50 MB
    """
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Delete old file if exists
    if content.audio_url:
        await content_service.delete_media(paragraph_id, language, "audio", content.audio_url)

    # Upload new file
    url = await content_service.upload_media(paragraph_id, language, "audio", file)

    # Update database
    content.audio_url = url
    content.status_audio = "ready"
    await repo.update(content)

    return {"audio_url": url, "status_audio": "ready"}


@router_school.post("/{paragraph_id}/content/slides")
async def upload_school_slides(
    paragraph_id: int,
    file: UploadFile = File(...),
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Upload slides file (PDF, PPTX) for a school paragraph.
    Max size: 50 MB
    """
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Delete old file if exists
    if content.slides_url:
        await content_service.delete_media(paragraph_id, language, "slides", content.slides_url)

    # Upload new file
    url = await content_service.upload_media(paragraph_id, language, "slides", file)

    # Update database
    content.slides_url = url
    content.status_slides = "ready"
    await repo.update(content)

    return {"slides_url": url, "status_slides": "ready"}


@router_school.post("/{paragraph_id}/content/video")
async def upload_school_video(
    paragraph_id: int,
    file: UploadFile = File(...),
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """
    Upload video file (MP4, WEBM) for a school paragraph.
    Max size: 200 MB
    """
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_or_create(paragraph_id, language)

    # Delete old file if exists
    if content.video_url:
        await content_service.delete_media(paragraph_id, language, "video", content.video_url)

    # Upload new file
    url = await content_service.upload_media(paragraph_id, language, "video", file)

    # Update database
    content.video_url = url
    content.status_video = "ready"
    await repo.update(content)

    return {"video_url": url, "status_video": "ready"}


@router_school.delete("/{paragraph_id}/content/audio")
async def delete_school_audio(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete audio file for a school paragraph."""
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content or not content.audio_url:
        raise HTTPException(status_code=404, detail="Audio not found")

    await content_service.delete_media(paragraph_id, language, "audio", content.audio_url)
    await repo.clear_media(content.id, "audio")

    return {"message": "Audio deleted"}


@router_school.delete("/{paragraph_id}/content/slides")
async def delete_school_slides(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete slides file for a school paragraph."""
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content or not content.slides_url:
        raise HTTPException(status_code=404, detail="Slides not found")

    await content_service.delete_media(paragraph_id, language, "slides", content.slides_url)
    await repo.clear_media(content.id, "slides")

    return {"message": "Slides deleted"}


@router_school.delete("/{paragraph_id}/content/video")
async def delete_school_video(
    paragraph_id: int,
    language: Literal["ru", "kk"] = Query(default="ru", description="Content language"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_admin),
):
    """Delete video file for a school paragraph."""
    await _get_paragraph_or_404(db, paragraph_id, school_id=current_user.school_id)

    repo = ParagraphContentRepository(db)
    content = await repo.get_by_paragraph_and_language(paragraph_id, language)

    if not content or not content.video_url:
        raise HTTPException(status_code=404, detail="Video not found")

    await content_service.delete_media(paragraph_id, language, "video", content.video_url)
    await repo.clear_media(content.id, "video")

    return {"message": "Video deleted"}
