"""
Student Mastery API endpoints.

This module provides endpoints for students to:
- View chapter mastery level (A/B/C grading)
- View mastery overview across all chapters
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
)
from app.models.user import User
from app.models.chapter import Chapter
from app.models.mastery import ChapterMastery
from app.repositories.chapter_mastery_repo import ChapterMasteryRepository
from app.schemas.mastery import (
    ChapterMasteryResponse,
    ChapterMasteryDetailResponse,
    MasteryOverviewResponse,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/mastery/chapter/{chapter_id}", response_model=ChapterMasteryResponse)
async def get_chapter_mastery(
    chapter_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapter mastery level (A/B/C grouping).

    Returns mastery record with:
    - A/B/C level and mastery_score (0-100)
    - Paragraph counters (total, completed, mastered, struggling)
    - Progress percentage
    - Summative test results (if taken)
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get chapter mastery record
    mastery_repo = ChapterMasteryRepository(db)
    mastery = await mastery_repo.get_by_student_chapter(
        student_id=student_id,
        chapter_id=chapter_id
    )

    if not mastery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter mastery not found for chapter {chapter_id}. Student hasn't started this chapter yet."
        )

    # Verify tenant isolation
    if mastery.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    logger.info(
        f"Student {student_id} retrieved chapter {chapter_id} mastery: "
        f"level={mastery.mastery_level}, score={mastery.mastery_score:.2f}"
    )

    return ChapterMasteryResponse.model_validate(mastery)


@router.get("/mastery/overview", response_model=MasteryOverviewResponse)
async def get_mastery_overview(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get mastery overview for all chapters.

    Returns:
    - List of all chapters with mastery data (A/B/C levels)
    - Aggregated statistics (level_a_count, level_b_count, level_c_count)
    - Average mastery score across all chapters
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get all chapter mastery records for student
    mastery_repo = ChapterMasteryRepository(db)
    mastery_records = await mastery_repo.get_by_student(
        student_id=student_id,
        school_id=school_id
    )

    # Batch fetch all chapters in one query (fixes N+1)
    chapter_ids = [m.chapter_id for m in mastery_records]
    chapters_map = {}
    if chapter_ids:
        chapters_result = await db.execute(
            select(Chapter).where(Chapter.id.in_(chapter_ids))
        )
        chapters_map = {c.id: c for c in chapters_result.scalars().all()}

    # Build chapters data with chapter info
    chapters_data = []
    for mastery in mastery_records:
        chapter = chapters_map.get(mastery.chapter_id)

        chapters_data.append(
            ChapterMasteryDetailResponse(
                id=mastery.id,
                student_id=mastery.student_id,
                chapter_id=mastery.chapter_id,
                total_paragraphs=mastery.total_paragraphs,
                completed_paragraphs=mastery.completed_paragraphs,
                mastered_paragraphs=mastery.mastered_paragraphs,
                struggling_paragraphs=mastery.struggling_paragraphs,
                mastery_level=mastery.mastery_level,
                mastery_score=mastery.mastery_score,
                progress_percentage=mastery.progress_percentage,
                summative_score=mastery.summative_score,
                summative_passed=mastery.summative_passed,
                last_updated_at=mastery.last_updated_at,
                chapter_title=chapter.title if chapter else None,
                chapter_order=chapter.order if chapter else None
            )
        )

    # Calculate aggregated stats
    total_chapters = len(mastery_records)
    level_a_count = sum(1 for m in mastery_records if m.mastery_level == 'A')
    level_b_count = sum(1 for m in mastery_records if m.mastery_level == 'B')
    level_c_count = sum(1 for m in mastery_records if m.mastery_level == 'C')

    if mastery_records:
        average_mastery_score = sum(m.mastery_score for m in mastery_records) / len(mastery_records)
    else:
        average_mastery_score = 0.0

    logger.info(
        f"Student {student_id} mastery overview: {total_chapters} chapters tracked, "
        f"A={level_a_count}, B={level_b_count}, C={level_c_count}, "
        f"avg_score={average_mastery_score:.2f}"
    )

    return MasteryOverviewResponse(
        student_id=student_id,
        chapters=chapters_data,
        total_chapters=total_chapters,
        average_mastery_score=round(average_mastery_score, 2),
        level_a_count=level_a_count,
        level_b_count=level_b_count,
        level_c_count=level_c_count
    )
