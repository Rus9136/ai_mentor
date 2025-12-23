"""
Student Content Browsing API endpoints.

This module provides endpoints for students to:
- Browse available textbooks with progress
- View chapters with mastery levels
- Read paragraphs with rich content
- Navigate between paragraphs
"""

import logging
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
)
from app.models.user import User
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.paragraph_content import ParagraphContent
from app.models.test import Test, TestPurpose
from app.models.mastery import ParagraphMastery, ChapterMastery
from app.models.learning import StudentParagraph as StudentParagraphModel
from app.repositories.textbook_repo import TextbookRepository
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


@router.get("/textbooks", response_model=List[StudentTextbookResponse])
async def get_student_textbooks(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available textbooks for student with progress.

    Returns global textbooks (school_id = NULL) and school-specific textbooks.
    Each textbook includes progress stats calculated from student's mastery data.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get textbooks: global (school_id = NULL) OR school-specific
    textbook_repo = TextbookRepository(db)
    textbooks = await textbook_repo.get_by_school(school_id=school_id, include_global=True)

    # Filter active textbooks only
    textbooks = [t for t in textbooks if t.is_active and not t.is_deleted]

    result = []

    for textbook in textbooks:
        # Get chapters count
        chapters_result = await db.execute(
            select(func.count(Chapter.id)).where(
                Chapter.textbook_id == textbook.id,
                Chapter.is_deleted == False
            )
        )
        chapters_count = chapters_result.scalar() or 0

        # Get total paragraphs count
        paragraphs_result = await db.execute(
            select(func.count(Paragraph.id))
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                Chapter.is_deleted == False,
                Paragraph.is_deleted == False
            )
        )
        paragraphs_total = paragraphs_result.scalar() or 0

        # Get student's completed paragraphs for this textbook
        completed_result = await db.execute(
            select(func.count(ParagraphMastery.id))
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
        )
        paragraphs_completed = completed_result.scalar() or 0

        # Get completed chapters
        chapters_completed = 0
        chapter_ids_result = await db.execute(
            select(Chapter.id).where(
                Chapter.textbook_id == textbook.id,
                Chapter.is_deleted == False
            )
        )
        chapter_ids = chapter_ids_result.scalars().all()

        for chapter_id in chapter_ids:
            ch_para_total = await db.execute(
                select(func.count(Paragraph.id)).where(
                    Paragraph.chapter_id == chapter_id,
                    Paragraph.is_deleted == False
                )
            )
            ch_para_total_count = ch_para_total.scalar() or 0

            if ch_para_total_count == 0:
                continue

            ch_para_completed = await db.execute(
                select(func.count(ParagraphMastery.id))
                .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
                .where(
                    Paragraph.chapter_id == chapter_id,
                    ParagraphMastery.student_id == student_id,
                    ParagraphMastery.is_completed == True
                )
            )
            ch_para_completed_count = ch_para_completed.scalar() or 0

            if ch_para_completed_count >= ch_para_total_count:
                chapters_completed += 1

        # Calculate percentage
        percentage = 0
        if paragraphs_total > 0:
            percentage = int((paragraphs_completed / paragraphs_total) * 100)

        # Get overall mastery level
        mastery_result = await db.execute(
            select(func.avg(ChapterMastery.mastery_score))
            .join(Chapter, ChapterMastery.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                ChapterMastery.student_id == student_id
            )
        )
        avg_mastery_score = mastery_result.scalar()

        mastery_level = None
        if avg_mastery_score is not None:
            if avg_mastery_score >= 85:
                mastery_level = "A"
            elif avg_mastery_score >= 60:
                mastery_level = "B"
            else:
                mastery_level = "C"

        # Get last activity
        last_activity_result = await db.execute(
            select(func.max(ParagraphMastery.last_updated_at))
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                ParagraphMastery.student_id == student_id
            )
        )
        last_activity = last_activity_result.scalar()

        result.append(
            StudentTextbookResponse(
                id=textbook.id,
                title=textbook.title,
                subject=textbook.subject,
                grade_level=textbook.grade_level,
                description=textbook.description,
                is_global=textbook.school_id is None,
                progress=StudentTextbookProgress(
                    chapters_total=chapters_count,
                    chapters_completed=chapters_completed,
                    paragraphs_total=paragraphs_total,
                    paragraphs_completed=paragraphs_completed,
                    percentage=percentage
                ),
                mastery_level=mastery_level,
                last_activity=last_activity,
                author=textbook.author,
                chapters_count=chapters_count
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} textbooks")
    return result


@router.get("/textbooks/{textbook_id}/chapters", response_model=List[StudentChapterResponse])
async def get_textbook_chapters(
    textbook_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapters for a textbook with student's progress.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Verify textbook access
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    # Get chapters ordered by order field
    chapters_result = await db.execute(
        select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.is_deleted == False
        ).order_by(Chapter.order)
    )
    chapters = chapters_result.scalars().all()

    result = []

    for idx, chapter in enumerate(chapters):
        # Get paragraphs count
        para_total_result = await db.execute(
            select(func.count(Paragraph.id)).where(
                Paragraph.chapter_id == chapter.id,
                Paragraph.is_deleted == False
            )
        )
        para_total = para_total_result.scalar() or 0

        # Get completed paragraphs
        para_completed_result = await db.execute(
            select(func.count(ParagraphMastery.id))
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .where(
                Paragraph.chapter_id == chapter.id,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
        )
        para_completed = para_completed_result.scalar() or 0

        percentage = 0
        if para_total > 0:
            percentage = int((para_completed / para_total) * 100)

        # Get chapter mastery
        mastery_result = await db.execute(
            select(ChapterMastery).where(
                ChapterMastery.chapter_id == chapter.id,
                ChapterMastery.student_id == student_id
            )
        )
        chapter_mastery = mastery_result.scalar_one_or_none()

        mastery_level = None
        mastery_score = None
        summative_passed = None

        if chapter_mastery:
            mastery_level = chapter_mastery.mastery_level
            mastery_score = chapter_mastery.mastery_score
            summative_passed = chapter_mastery.summative_passed

        # Determine chapter status
        if para_completed >= para_total and para_total > 0:
            chapter_status = "completed"
        elif para_completed > 0:
            chapter_status = "in_progress"
        else:
            if idx == 0:
                chapter_status = "not_started"
            else:
                prev_chapter = chapters[idx - 1]
                prev_para_total_result = await db.execute(
                    select(func.count(Paragraph.id)).where(
                        Paragraph.chapter_id == prev_chapter.id,
                        Paragraph.is_deleted == False
                    )
                )
                prev_para_total = prev_para_total_result.scalar() or 0

                prev_para_completed_result = await db.execute(
                    select(func.count(ParagraphMastery.id))
                    .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
                    .where(
                        Paragraph.chapter_id == prev_chapter.id,
                        ParagraphMastery.student_id == student_id,
                        ParagraphMastery.is_completed == True
                    )
                )
                prev_para_completed = prev_para_completed_result.scalar() or 0

                if prev_para_completed >= prev_para_total and prev_para_total > 0:
                    chapter_status = "not_started"
                else:
                    chapter_status = "locked"

        # Check for summative test
        test_result = await db.execute(
            select(func.count(Test.id)).where(
                Test.chapter_id == chapter.id,
                Test.test_purpose == TestPurpose.SUMMATIVE,
                Test.is_active == True,
                Test.is_deleted == False
            )
        )
        has_summative_test = (test_result.scalar() or 0) > 0

        result.append(
            StudentChapterResponse(
                id=chapter.id,
                textbook_id=chapter.textbook_id,
                title=chapter.title,
                number=chapter.number,
                order=chapter.order,
                description=chapter.description,
                learning_objective=chapter.learning_objective,
                status=chapter_status,
                progress=StudentChapterProgress(
                    paragraphs_total=para_total,
                    paragraphs_completed=para_completed,
                    percentage=percentage
                ),
                mastery_level=mastery_level,
                mastery_score=mastery_score,
                has_summative_test=has_summative_test,
                summative_passed=summative_passed
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} chapters for textbook {textbook_id}")
    return result


@router.get("/chapters/{chapter_id}/paragraphs", response_model=List[StudentParagraphResponse])
async def get_chapter_paragraphs(
    chapter_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paragraphs for a chapter with student's progress.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get chapter with textbook info
    chapter_result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.textbook))
        .where(Chapter.id == chapter_id, Chapter.is_deleted == False)
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    textbook = chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    # Get paragraphs ordered
    paragraphs_result = await db.execute(
        select(Paragraph).where(
            Paragraph.chapter_id == chapter_id,
            Paragraph.is_deleted == False
        ).order_by(Paragraph.order)
    )
    paragraphs = paragraphs_result.scalars().all()

    result = []

    for para in paragraphs:
        # Get mastery info
        mastery_result = await db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.paragraph_id == para.id,
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

        practice_score = None
        if mastery and mastery.best_score is not None:
            practice_score = mastery.best_score

        # Estimate time
        word_count = len(para.content.split()) if para.content else 0
        estimated_time = max(3, min(15, word_count // 200 + 3))

        # Check for practice test
        test_result = await db.execute(
            select(func.count(Test.id)).where(
                Test.paragraph_id == para.id,
                Test.test_purpose.in_([TestPurpose.FORMATIVE, TestPurpose.PRACTICE]),
                Test.is_active == True,
                Test.is_deleted == False
            )
        )
        has_practice = (test_result.scalar() or 0) > 0

        result.append(
            StudentParagraphResponse(
                id=para.id,
                chapter_id=para.chapter_id,
                title=para.title,
                number=para.number,
                order=para.order,
                summary=para.summary,
                status=para_status,
                estimated_time=estimated_time,
                has_practice=has_practice,
                practice_score=practice_score,
                learning_objective=para.learning_objective,
                key_terms=para.key_terms
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} paragraphs for chapter {chapter_id}")
    return result


@router.get("/paragraphs/{paragraph_id}", response_model=StudentParagraphDetailResponse)
async def get_paragraph_detail(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full paragraph content for learning.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get paragraph with chapter and textbook
    para_result = await db.execute(
        select(Paragraph)
        .options(
            selectinload(Paragraph.chapter).selectinload(Chapter.textbook),
            selectinload(Paragraph.contents)
        )
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

    # Get mastery info
    mastery_result = await db.execute(
        select(ParagraphMastery).where(
            ParagraphMastery.paragraph_id == paragraph_id,
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

    for content in paragraph.contents:
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
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            last_accessed_at=datetime.now(timezone.utc)
        )
        db.add(student_para)
    else:
        student_para.last_accessed_at = datetime.now(timezone.utc)

    await db.commit()

    logger.info(f"Student {student_id} accessed paragraph {paragraph_id}")

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
        chapter_title=paragraph.chapter.title,
        textbook_title=textbook.title
    )


@router.get("/paragraphs/{paragraph_id}/content", response_model=ParagraphRichContent)
async def get_paragraph_rich_content(
    paragraph_id: int,
    language: str = Query("ru", description="Content language: ru or kk"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get rich content for a paragraph (audio, video, slides, cards).
    """
    student = await get_student_from_user(current_user, db)

    if language not in ("ru", "kk"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be 'ru' or 'kk'"
        )

    # Get paragraph with chapter
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
            has_cards=content.cards is not None and len(content.cards) > 0
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
            has_cards=False
        )


@router.get("/paragraphs/{paragraph_id}/navigation", response_model=ParagraphNavigationContext)
async def get_paragraph_navigation(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get navigation context for paragraph learning view.

    Includes previous/next paragraph IDs, chapter info, and position.
    """
    # Get paragraph with chapter and textbook
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

    chapter = paragraph.chapter

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
        if p.id == paragraph_id:
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
        current_paragraph_id=paragraph_id,
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
        current_position_in_chapter=(current_idx or 0) + 1
    )
