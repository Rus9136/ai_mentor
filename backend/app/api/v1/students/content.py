"""
Student Content Browsing API endpoints.

This module provides endpoints for students to:
- Browse available textbooks with progress
- View chapters with mastery levels
- Read paragraphs with rich content
- Navigate between paragraphs

Refactored in Phase 4 to use StudentContentService with batch queries.
"""

import logging
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
    get_student_content_service,
    get_textbook_with_access,
    get_chapter_with_access,
    get_paragraph_with_access,
    get_pagination_params,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.models.user import User
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.paragraph_content import ParagraphContent
from app.models.mastery import ParagraphMastery
from app.models.learning import StudentParagraph as StudentParagraphModel
from app.services.student_content_service import StudentContentService
from app.schemas.student_content import (
    StudentTextbookResponse,
    StudentTextbookProgress,
    StudentChapterResponse,
    StudentChapterProgress,
    StudentParagraphResponse,
    StudentParagraphDetailResponse,
    ParagraphRichContent,
    ParagraphNavigationContext,
    FlashCard,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/textbooks", response_model=PaginatedResponse[StudentTextbookResponse])
async def get_student_textbooks(
    pagination: PaginationParams = Depends(get_pagination_params),
    subject_id: int = Query(None, description="Filter by subject ID"),
    grade_level: int = Query(None, ge=1, le=11, description="Filter by grade level (1-11)"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
    service: StudentContentService = Depends(get_student_content_service),
):
    """
    Get available textbooks for student with progress.

    Returns global textbooks (school_id = NULL) and school-specific textbooks.
    Each textbook includes progress stats calculated from student's mastery data.

    Uses batch queries for performance (no N+1 problem).
    Supports pagination with `page` and `page_size` query parameters.

    Filters:
    - subject_id: Filter by subject
    - grade_level: Filter by grade level (1-11)
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get textbooks with progress using batch queries
    textbooks_data, total = await service.get_textbooks_with_progress(
        student_id,
        school_id,
        page=pagination.page,
        page_size=pagination.page_size,
        subject_id=subject_id,
        grade_level=grade_level,
    )

    result = []
    for item in textbooks_data:
        textbook = item["textbook"]
        progress = item["progress"]

        result.append(
            StudentTextbookResponse(
                id=textbook.id,
                title=textbook.title,
                subject_id=textbook.subject_id,
                subject=textbook.subject,
                subject_rel=textbook.subject_rel,
                grade_level=textbook.grade_level,
                description=textbook.description,
                is_global=textbook.school_id is None,
                progress=StudentTextbookProgress(
                    chapters_total=progress["chapters_total"],
                    chapters_completed=progress["chapters_completed"],
                    paragraphs_total=progress["paragraphs_total"],
                    paragraphs_completed=progress["paragraphs_completed"],
                    percentage=progress["percentage"],
                ),
                mastery_level=item["mastery_level"],
                last_activity=item["last_activity"],
                author=textbook.author,
                chapters_count=progress["chapters_total"],
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} textbooks")
    return PaginatedResponse.create(result, total, pagination.page, pagination.page_size)


@router.get("/textbooks/{textbook_id}/chapters", response_model=PaginatedResponse[StudentChapterResponse])
async def get_textbook_chapters(
    textbook: Textbook = Depends(get_textbook_with_access),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
    service: StudentContentService = Depends(get_student_content_service),
):
    """
    Get chapters for a textbook with student's progress.

    Uses batch queries for performance (no N+1 problem).
    Supports pagination with `page` and `page_size` query parameters.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get chapters with progress using batch queries
    chapters_data, total = await service.get_chapters_with_progress(
        textbook.id, student_id, school_id, page=pagination.page, page_size=pagination.page_size
    )

    result = []
    for item in chapters_data:
        chapter = item["chapter"]
        progress = item["progress"]

        result.append(
            StudentChapterResponse(
                id=chapter.id,
                textbook_id=chapter.textbook_id,
                title=chapter.title,
                number=chapter.number,
                order=chapter.order,
                description=chapter.description,
                learning_objective=chapter.learning_objective,
                status=item["status"],
                progress=StudentChapterProgress(
                    paragraphs_total=progress["paragraphs_total"],
                    paragraphs_completed=progress["paragraphs_completed"],
                    percentage=progress["percentage"],
                ),
                mastery_level=item["mastery_level"],
                mastery_score=item["mastery_score"],
                has_summative_test=item["has_summative_test"],
                summative_passed=item["summative_passed"],
            )
        )

    logger.info(
        f"Student {student_id} retrieved {len(result)} chapters "
        f"for textbook {textbook.id}"
    )
    return PaginatedResponse.create(result, total, pagination.page, pagination.page_size)


@router.get("/chapters/{chapter_id}/paragraphs", response_model=PaginatedResponse[StudentParagraphResponse])
async def get_chapter_paragraphs(
    chapter: Chapter = Depends(get_chapter_with_access),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
    service: StudentContentService = Depends(get_student_content_service),
):
    """
    Get paragraphs for a chapter with student's progress.

    Uses batch queries for performance (no N+1 problem).
    Supports pagination with `page` and `page_size` query parameters.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get paragraphs with progress using batch queries
    paragraphs_data, total = await service.get_paragraphs_with_progress(
        chapter.id, student_id, school_id, page=pagination.page, page_size=pagination.page_size
    )

    result = []
    for item in paragraphs_data:
        para = item["paragraph"]

        result.append(
            StudentParagraphResponse(
                id=para.id,
                chapter_id=para.chapter_id,
                title=para.title,
                number=para.number,
                order=para.order,
                summary=para.summary,
                status=item["status"],
                estimated_time=item["estimated_time"],
                has_practice=item["has_practice"],
                practice_score=item["practice_score"],
                learning_objective=para.learning_objective,
                key_terms=para.key_terms,
            )
        )

    logger.info(
        f"Student {student_id} retrieved {len(result)} paragraphs "
        f"for chapter {chapter.id}"
    )
    return PaginatedResponse.create(result, total, pagination.page, pagination.page_size)


@router.get("/paragraphs/{paragraph_id}", response_model=StudentParagraphDetailResponse)
async def get_paragraph_detail(
    paragraph: Paragraph = Depends(get_paragraph_with_access),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get full paragraph content for learning.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Load contents for paragraph
    contents_result = await db.execute(
        select(ParagraphContent).where(
            ParagraphContent.paragraph_id == paragraph.id
        )
    )
    contents = contents_result.scalars().all()

    # Get mastery info
    mastery_result = await db.execute(
        select(ParagraphMastery).where(
            ParagraphMastery.paragraph_id == paragraph.id,
            ParagraphMastery.student_id == student_id
        )
    )
    mastery = mastery_result.scalar_one_or_none()

    if mastery and mastery.is_completed:
        para_status = "completed"
    elif mastery:
        para_status = "in_progress"
    else:
        para_status = "not_started"

    # Check rich content availability
    has_audio = False
    has_video = False
    has_slides = False
    has_cards = False

    for content in contents:
        if content.audio_url:
            has_audio = True
        if content.video_url:
            has_video = True
        if content.slides_url:
            has_slides = True
        if content.cards:
            has_cards = True

    # Update last accessed
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph.id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph.id,
            school_id=school_id,
            last_accessed_at=datetime.now(timezone.utc)
        )
        db.add(student_para)
    else:
        student_para.last_accessed_at = datetime.now(timezone.utc)

    await db.commit()

    # Get chapter and textbook titles from eager-loaded relationship
    chapter = paragraph.chapter
    textbook = chapter.textbook

    logger.info(f"Student {student_id} accessed paragraph {paragraph.id}")

    return StudentParagraphDetailResponse(
        id=paragraph.id,
        chapter_id=paragraph.chapter_id,
        title=paragraph.title,
        number=paragraph.number,
        order=paragraph.order,
        content=paragraph.content,
        summary=paragraph.summary,
        learning_objective=paragraph.learning_objective,
        lesson_objective=paragraph.lesson_objective,
        key_terms=paragraph.key_terms,
        questions=paragraph.questions,
        status=para_status,
        current_step=None,
        has_audio=has_audio,
        has_video=has_video,
        has_slides=has_slides,
        has_cards=has_cards,
        chapter_title=chapter.title,
        textbook_title=textbook.title,
    )


@router.get("/paragraphs/{paragraph_id}/content", response_model=ParagraphRichContent)
async def get_paragraph_rich_content(
    paragraph_id: int,
    language: str = Query("ru", description="Content language: ru or kk"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get rich content for a paragraph (audio, video, slides, cards).
    """
    _ = await get_student_from_user(current_user, db)

    if language not in ("ru", "kk"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be 'ru' or 'kk'"
        )

    # Get paragraph with access check
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get content for requested language
    content_result = await db.execute(
        select(ParagraphContent).where(
            ParagraphContent.paragraph_id == paragraph_id,
            ParagraphContent.language == language
        )
    )
    content = content_result.scalar_one_or_none()

    if content:
        cards = None
        if content.cards:
            cards = [FlashCard(**card) for card in content.cards]

        return ParagraphRichContent(
            paragraph_id=paragraph_id,
            language=language,
            explain_text=content.explain_text,
            audio_url=content.audio_url,
            video_url=content.video_url,
            slides_url=content.slides_url,
            cards=cards,
            has_explain=content.explain_text is not None,
            has_audio=content.audio_url is not None,
            has_video=content.video_url is not None,
            has_slides=content.slides_url is not None,
            has_cards=content.cards is not None and len(content.cards) > 0,
        )
    else:
        return ParagraphRichContent(
            paragraph_id=paragraph_id,
            language=language,
            explain_text=None,
            audio_url=None,
            video_url=None,
            slides_url=None,
            cards=None,
            has_explain=False,
            has_audio=False,
            has_video=False,
            has_slides=False,
            has_cards=False,
        )


@router.get("/paragraphs/{paragraph_id}/navigation", response_model=ParagraphNavigationContext)
async def get_paragraph_navigation(
    paragraph: Paragraph = Depends(get_paragraph_with_access),
    current_user: User = Depends(require_student),
    db: AsyncSession = Depends(get_db),
):
    """
    Get navigation context for paragraph learning view.

    Includes previous/next paragraph IDs, chapter info, and position.
    """
    chapter = paragraph.chapter
    textbook = chapter.textbook

    # Get all paragraphs in chapter ordered
    all_paras_result = await db.execute(
        select(Paragraph).where(
            Paragraph.chapter_id == chapter.id,
            Paragraph.is_deleted == False
        ).order_by(Paragraph.order)
    )
    all_paragraphs = all_paras_result.scalars().all()

    # Find current position and neighbors
    current_idx = None
    for idx, p in enumerate(all_paragraphs):
        if p.id == paragraph.id:
            current_idx = idx
            break

    previous_id = None
    next_id = None

    if current_idx is not None:
        if current_idx > 0:
            previous_id = all_paragraphs[current_idx - 1].id
        if current_idx < len(all_paragraphs) - 1:
            next_id = all_paragraphs[current_idx + 1].id

    return ParagraphNavigationContext(
        current_paragraph_id=paragraph.id,
        current_paragraph_number=paragraph.number,
        current_paragraph_title=paragraph.title,
        chapter_id=chapter.id,
        chapter_title=chapter.title,
        chapter_number=chapter.number,
        textbook_id=textbook.id,
        textbook_title=textbook.title,
        previous_paragraph_id=previous_id,
        next_paragraph_id=next_id,
        total_paragraphs_in_chapter=len(all_paragraphs),
        current_position_in_chapter=(current_idx or 0) + 1,
    )
