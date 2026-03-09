"""
Student Spaced Repetition (Review) API endpoints.

Endpoints for students to:
- View paragraphs due for review today
- Submit review quiz results
- View review statistics
"""

import logging
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.dependencies import require_student, get_current_user_school_id, get_student_from_user
from app.models.user import User
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.models.mastery import ParagraphMastery
from app.repositories.review_schedule_repo import ReviewScheduleRepository
from app.services.spaced_repetition_service import SpacedRepetitionService
from app.schemas.review_schedule import (
    DueReviewsResponse,
    ReviewItemResponse,
    ReviewResultRequest,
    ReviewResultResponse,
    ReviewStatsResponse,
)

router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/reviews/due", response_model=DueReviewsResponse)
async def get_due_reviews(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get paragraphs due for review today.

    Returns list of paragraphs needing review with context
    (paragraph title, chapter, textbook, mastery info).
    """
    student = await get_student_from_user(current_user, db)
    review_repo = ReviewScheduleRepository(db)

    # Get due reviews
    due_reviews = await review_repo.get_due_reviews(student.id)
    upcoming_count = await review_repo.get_upcoming_count(student.id, days=7)
    total_active = await review_repo.get_active_count(student.id)

    # Enrich with paragraph info
    items = []
    for review in due_reviews:
        # Load paragraph with chapter and textbook
        para_result = await db.execute(
            select(Paragraph)
            .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
            .where(Paragraph.id == review.paragraph_id)
        )
        paragraph = para_result.scalar_one_or_none()

        # Get mastery info
        mastery_result = await db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.student_id == student.id,
                ParagraphMastery.paragraph_id == review.paragraph_id,
            )
        )
        mastery = mastery_result.scalar_one_or_none()

        items.append(ReviewItemResponse(
            id=review.id,
            paragraph_id=review.paragraph_id,
            paragraph_title=paragraph.title if paragraph else None,
            paragraph_number=paragraph.number if paragraph else None,
            chapter_title=paragraph.chapter.title if paragraph and paragraph.chapter else None,
            textbook_title=paragraph.chapter.textbook.title if paragraph and paragraph.chapter and paragraph.chapter.textbook else None,
            streak=review.streak,
            next_review_date=review.next_review_date,
            last_review_date=review.last_review_date,
            total_reviews=review.total_reviews,
            successful_reviews=review.successful_reviews,
            best_score=mastery.best_score if mastery else None,
            effective_score=mastery.effective_score if mastery else None,
        ))

    return DueReviewsResponse(
        due_today=items,
        due_today_count=len(items),
        upcoming_week_count=upcoming_count,
        total_active=total_active,
    )


@router.post("/reviews/{paragraph_id}/complete", response_model=ReviewResultResponse)
async def submit_review_result(
    paragraph_id: int,
    request: ReviewResultRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Submit the result of a review quiz for a paragraph.

    The score determines whether the review was successful:
    - >= 80%: passed, streak increases, interval grows
    - < 80%: failed, streak decreases by 2, review scheduled sooner
    """
    student = await get_student_from_user(current_user, db)

    service = SpacedRepetitionService(db)

    try:
        result = await service.process_review_result(
            student_id=student.id,
            paragraph_id=paragraph_id,
            score=request.score,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return ReviewResultResponse(
        paragraph_id=paragraph_id,
        passed=result["passed"],
        score=result["score"],
        new_streak=result["new_streak"],
        next_review_date=result["next_review_date"],
        message=result["message"],
    )


@router.get("/reviews/stats", response_model=ReviewStatsResponse)
async def get_review_stats(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get student's spaced repetition statistics."""
    student = await get_student_from_user(current_user, db)
    review_repo = ReviewScheduleRepository(db)

    stats = await review_repo.get_stats(student.id)
    due_today = len(await review_repo.get_due_reviews(student.id))
    due_week = await review_repo.get_upcoming_count(student.id, days=7) + due_today

    return ReviewStatsResponse(
        total_active_reviews=stats["total_active"],
        due_today=due_today,
        due_this_week=due_week,
        total_completed_reviews=stats["total_reviews"],
        success_rate=round(stats["success_rate"], 2),
        average_streak=round(stats["avg_streak"], 1),
    )
