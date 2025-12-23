"""
Student Embedded Questions API endpoints.

This module provides endpoints for students to:
- View embedded questions for a paragraph (without answers)
- Submit answers to embedded questions
"""

import logging
from typing import List
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
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
from app.models.embedded_question import EmbeddedQuestion, StudentEmbeddedAnswer
from app.schemas.embedded_question import (
    EmbeddedQuestionForStudent,
    AnswerEmbeddedQuestionRequest,
    AnswerEmbeddedQuestionResponse,
)


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/paragraphs/{paragraph_id}/embedded-questions", response_model=List[EmbeddedQuestionForStudent])
async def get_embedded_questions(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get embedded questions for a paragraph (without correct answers).

    These are "Check yourself" questions shown during paragraph reading.
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

    # Get active embedded questions
    questions_result = await db.execute(
        select(EmbeddedQuestion).where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            EmbeddedQuestion.is_active == True
        ).order_by(EmbeddedQuestion.sort_order)
    )
    questions = questions_result.scalars().all()

    # Convert to student-safe format (without is_correct)
    result = []
    for q in questions:
        result.append(EmbeddedQuestionForStudent.from_question(q))

    return result


@router.post("/embedded-questions/{question_id}/answer", response_model=AnswerEmbeddedQuestionResponse)
async def answer_embedded_question(
    question_id: int,
    request: AnswerEmbeddedQuestionRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit answer to an embedded question.

    For single_choice/true_false: answer should be a string (option id or "true"/"false")
    For multiple_choice: answer should be a list of option ids

    Returns:
        Whether answer is correct, explanation, and correct answer
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get question
    question_result = await db.execute(
        select(EmbeddedQuestion).where(
            EmbeddedQuestion.id == question_id,
            EmbeddedQuestion.is_active == True
        )
    )
    question = question_result.scalar_one_or_none()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify access through paragraph -> chapter -> textbook
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == question.paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question's paragraph not found"
        )

    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check answer
    is_correct = question.check_answer(request.answer)

    # Get correct answer for response
    correct_answer = None
    if question.question_type == "true_false":
        correct_answer = question.correct_answer
    elif question.options:
        if question.question_type == "single_choice":
            for opt in question.options:
                if opt.get("is_correct"):
                    correct_answer = opt.get("id")
                    break
        else:  # multiple_choice
            correct_answer = [opt.get("id") for opt in question.options if opt.get("is_correct")]

    # Save or update student's answer
    existing_answer_result = await db.execute(
        select(StudentEmbeddedAnswer).where(
            StudentEmbeddedAnswer.student_id == student_id,
            StudentEmbeddedAnswer.question_id == question_id
        )
    )
    existing_answer = existing_answer_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if existing_answer:
        # Update existing answer
        existing_answer.is_correct = is_correct
        existing_answer.attempts_count += 1
        existing_answer.answered_at = now
        if isinstance(request.answer, list):
            existing_answer.selected_options = request.answer
            existing_answer.selected_answer = None
        else:
            existing_answer.selected_answer = str(request.answer)
            existing_answer.selected_options = None
        attempts_count = existing_answer.attempts_count
    else:
        # Create new answer
        new_answer = StudentEmbeddedAnswer(
            student_id=student_id,
            question_id=question_id,
            school_id=school_id,
            is_correct=is_correct,
            answered_at=now,
            attempts_count=1
        )
        if isinstance(request.answer, list):
            new_answer.selected_options = request.answer
        else:
            new_answer.selected_answer = str(request.answer)
        db.add(new_answer)
        attempts_count = 1

    await db.commit()

    logger.info(
        f"Student {student_id} answered embedded question {question_id}: "
        f"correct={is_correct}, attempts={attempts_count}"
    )

    return AnswerEmbeddedQuestionResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        explanation=question.explanation,
        attempts_count=attempts_count
    )
