"""
Student Learning Progress API endpoints.

This module provides endpoints for students to:
- Track paragraph learning progress (steps)
- Submit self-assessments
- View current learning step
"""

import logging
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
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
from app.schemas.embedded_question import (
    SelfAssessmentRequest,
    SelfAssessmentResponse,
    UpdateStepRequest,
    StepProgressResponse,
    ParagraphProgressResponse,
)


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

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            current_step=request.step,
            time_spent=request.time_spent or 0,
            last_accessed_at=now
        )
        db.add(student_para)
    else:
        student_para.current_step = request.step
        student_para.last_accessed_at = now
        if request.time_spent:
            student_para.time_spent += request.time_spent

    # Mark as completed if step is 'completed'
    if request.step == "completed":
        student_para.is_completed = True
        student_para.completed_at = now

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
    - understood: All clear
    - questions: Have questions
    - difficult: Difficult to understand
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

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            self_assessment=request.rating,
            self_assessment_at=now,
            last_accessed_at=now
        )
        db.add(student_para)
    else:
        student_para.self_assessment = request.rating
        student_para.self_assessment_at = now
        student_para.last_accessed_at = now

    await db.commit()

    logger.info(f"Student {student_id} submitted self-assessment '{request.rating}' for paragraph {paragraph_id}")

    messages = {
        "understood": "Отлично! Продолжай в том же духе!",
        "questions": "Хорошо, попробуй повторить материал или задай вопрос.",
        "difficult": "Не переживай! Попробуй посмотреть материал в другом формате."
    }

    return SelfAssessmentResponse(
        paragraph_id=paragraph_id,
        rating=request.rating,
        recorded_at=now,
        message=messages.get(request.rating, "Оценка сохранена")
    )
