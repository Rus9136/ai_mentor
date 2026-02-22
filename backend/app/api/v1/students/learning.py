"""
Student Learning Progress API endpoints.

This module provides endpoints for students to:
- Track paragraph learning progress (steps)
- Submit self-assessments
- View current learning step
- View overall learning progress summary
"""

import logging
from datetime import datetime, timezone
from typing import Optional

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
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.models.learning import StudentParagraph as StudentParagraphModel
from app.models.embedded_question import EmbeddedQuestion, StudentEmbeddedAnswer
from app.models.mastery import ParagraphMastery
from app.models.test_attempt import TestAttempt, AttemptStatus
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository
from app.schemas.embedded_question import (
    SelfAssessmentRequest,
    SelfAssessmentResponse,
    UpdateStepRequest,
    StepProgressResponse,
    ParagraphProgressResponse,
)
from app.schemas.test_attempt import StudentProgressResponse
from app.services.self_assessment_service import SelfAssessmentService


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/paragraphs/{paragraph_id}/progress", response_model=ParagraphProgressResponse)
async def get_paragraph_progress(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student's progress for a paragraph including step tracking.

    Returns:
        Progress with current step, time spent, and embedded questions stats
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get paragraph to verify access
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

    # Get student's paragraph progress
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    # Determine available steps based on paragraph content
    available_steps = ["intro", "content"]

    # Check if paragraph has embedded questions (practice step)
    eq_count_result = await db.execute(
        select(func.count(EmbeddedQuestion.id)).where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            EmbeddedQuestion.is_active == True
        )
    )
    embedded_questions_total = eq_count_result.scalar() or 0

    if embedded_questions_total > 0:
        available_steps.append("practice")

    # Add summary step if paragraph has summary
    if paragraph.summary:
        available_steps.append("summary")

    # Get embedded questions answered by student
    answered_result = await db.execute(
        select(func.count(StudentEmbeddedAnswer.id))
        .join(EmbeddedQuestion, StudentEmbeddedAnswer.question_id == EmbeddedQuestion.id)
        .where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            StudentEmbeddedAnswer.student_id == student_id
        )
    )
    embedded_questions_answered = answered_result.scalar() or 0

    # Get correct answers count
    correct_result = await db.execute(
        select(func.count(StudentEmbeddedAnswer.id))
        .join(EmbeddedQuestion, StudentEmbeddedAnswer.question_id == EmbeddedQuestion.id)
        .where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            StudentEmbeddedAnswer.student_id == student_id,
            StudentEmbeddedAnswer.is_correct == True
        )
    )
    embedded_questions_correct = correct_result.scalar() or 0

    if student_para:
        return ParagraphProgressResponse(
            paragraph_id=paragraph_id,
            is_completed=student_para.is_completed,
            current_step=student_para.current_step or "intro",
            time_spent=student_para.time_spent,
            last_accessed_at=student_para.last_accessed_at,
            completed_at=student_para.completed_at,
            self_assessment=student_para.self_assessment,
            self_assessment_at=student_para.self_assessment_at,
            available_steps=available_steps,
            embedded_questions_total=embedded_questions_total,
            embedded_questions_answered=embedded_questions_answered,
            embedded_questions_correct=embedded_questions_correct
        )
    else:
        return ParagraphProgressResponse(
            paragraph_id=paragraph_id,
            is_completed=False,
            current_step="intro",
            time_spent=0,
            last_accessed_at=None,
            completed_at=None,
            self_assessment=None,
            self_assessment_at=None,
            available_steps=available_steps,
            embedded_questions_total=embedded_questions_total,
            embedded_questions_answered=embedded_questions_answered,
            embedded_questions_correct=embedded_questions_correct
        )


@router.post("/paragraphs/{paragraph_id}/progress", response_model=StepProgressResponse)
async def update_paragraph_progress(
    paragraph_id: int,
    request: UpdateStepRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student's progress step for a paragraph.

    Steps: intro -> content -> practice -> summary -> completed
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get paragraph to verify access
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

    # Get or create student's paragraph progress
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    # Validate time_spent (additional server-side check)
    validated_time_spent = 0
    if request.time_spent is not None and 0 < request.time_spent <= 3600:
        validated_time_spent = request.time_spent

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            current_step=request.step,
            time_spent=validated_time_spent,
            last_accessed_at=now
        )
        db.add(student_para)
    else:
        student_para.current_step = request.step
        student_para.last_accessed_at = now
        if validated_time_spent > 0:
            student_para.time_spent += validated_time_spent

    # Mark as completed if step is 'completed'
    if request.step == "completed":
        student_para.is_completed = True
        student_para.completed_at = now

        # Also update paragraph_mastery so chapter/textbook lists show completion
        mastery_repo = ParagraphMasteryRepository(db)
        await mastery_repo.upsert(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            is_completed=True,
            completed_at=now,
        )

    await db.commit()
    await db.refresh(student_para)

    # Determine available steps
    available_steps = ["intro", "content"]
    eq_count_result = await db.execute(
        select(func.count(EmbeddedQuestion.id)).where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            EmbeddedQuestion.is_active == True
        )
    )
    if (eq_count_result.scalar() or 0) > 0:
        available_steps.append("practice")
    if paragraph.summary:
        available_steps.append("summary")

    logger.info(f"Student {student_id} updated paragraph {paragraph_id} progress to step '{request.step}'")

    return StepProgressResponse(
        paragraph_id=paragraph_id,
        current_step=student_para.current_step,
        is_completed=student_para.is_completed,
        time_spent=student_para.time_spent,
        available_steps=available_steps,
        self_assessment=student_para.self_assessment
    )


@router.post("/paragraphs/{paragraph_id}/self-assessment", response_model=SelfAssessmentResponse)
async def submit_self_assessment(
    paragraph_id: int,
    request: SelfAssessmentRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit self-assessment for a paragraph.

    Rating options:
    - understood: All clear -> +5.0 impact, recommendation: next_paragraph
    - questions: Have questions -> 0.0 impact, recommendation: chat_tutor
    - difficult: Difficult -> -5.0 impact, recommendation: review

    Creates an append-only history record and returns mastery_impact
    and next_recommendation for the mobile app.
    """
    student = await get_student_from_user(current_user, db)

    # Get paragraph to verify access
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

    # Delegate to service
    service = SelfAssessmentService(db)
    assessment, next_recommendation = await service.submit_assessment(
        student_id=student.id,
        paragraph_id=paragraph_id,
        school_id=school_id,
        rating=request.rating,
        practice_score=request.practice_score,
        time_spent=request.time_spent,
    )

    logger.info(f"Student {student.id} submitted self-assessment '{request.rating}' for paragraph {paragraph_id}")

    return SelfAssessmentResponse(
        id=assessment.id,
        paragraph_id=paragraph_id,
        rating=request.rating,
        practice_score=assessment.practice_score,
        mastery_impact=assessment.mastery_impact,
        next_recommendation=next_recommendation,
        created_at=assessment.created_at,
    )


@router.get("/progress", response_model=StudentProgressResponse)
async def get_student_progress(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    chapter_id: Optional[int] = Query(None, description="Filter by chapter ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student learning progress summary.

    Returns paragraph-level mastery statistics:
    - Total paragraphs
    - Completed paragraphs
    - Mastered paragraphs (status = 'mastered')
    - Struggling paragraphs (status = 'struggling')
    - Average and best scores
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    mastery_repo = ParagraphMasteryRepository(db)
    mastery_records = await mastery_repo.get_by_student(
        student_id=student_id,
        school_id=school_id
    )

    chapter_name = None
    if chapter_id:
        result = await db.execute(
            select(Paragraph.id).where(
                Paragraph.chapter_id == chapter_id,
                Paragraph.is_deleted == False
            )
        )
        paragraph_ids = set(result.scalars().all())
        mastery_records = [m for m in mastery_records if m.paragraph_id in paragraph_ids]

        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        chapter_name = chapter.title if chapter else None

    total_paragraphs = len(mastery_records)
    completed_paragraphs = sum(1 for m in mastery_records if m.is_completed)
    mastered_paragraphs = sum(1 for m in mastery_records if m.status == 'mastered')
    struggling_paragraphs = sum(1 for m in mastery_records if m.status == 'struggling')

    if mastery_records:
        average_score = sum(m.average_score or 0.0 for m in mastery_records) / len(mastery_records)
        best_score = max((m.best_score for m in mastery_records if m.best_score is not None), default=None)
    else:
        average_score = 0.0
        best_score = None

    result = await db.execute(
        select(func.count(TestAttempt.id)).where(
            TestAttempt.student_id == student_id,
            TestAttempt.school_id == school_id,
            TestAttempt.status == AttemptStatus.COMPLETED
        )
    )
    total_attempts = result.scalar() or 0

    paragraphs_data = []
    for mastery in mastery_records:
        paragraph_result = await db.execute(
            select(Paragraph).where(Paragraph.id == mastery.paragraph_id)
        )
        paragraph = paragraph_result.scalar_one_or_none()

        paragraphs_data.append({
            "paragraph_id": mastery.paragraph_id,
            "paragraph_title": paragraph.title if paragraph else None,
            "paragraph_number": paragraph.number if paragraph else None,
            "status": mastery.status,
            "average_score": mastery.average_score,
            "best_score": mastery.best_score,
            "is_completed": mastery.is_completed,
            "attempts_count": mastery.attempts_count,
            "time_spent": mastery.time_spent
        })

    logger.info(
        f"Student {student_id} progress: {mastered_paragraphs}/{total_paragraphs} mastered, "
        f"avg_score={average_score:.2f}"
    )

    return StudentProgressResponse(
        chapter_id=chapter_id,
        chapter_name=chapter_name,
        total_paragraphs=total_paragraphs,
        completed_paragraphs=completed_paragraphs,
        mastered_paragraphs=mastered_paragraphs,
        struggling_paragraphs=struggling_paragraphs,
        average_score=average_score,
        best_score=best_score,
        total_attempts=total_attempts,
        paragraphs=paragraphs_data
    )
