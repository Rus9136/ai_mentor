"""
Repository for StudentTaskAnswer operations.
"""
from typing import Optional, List
from datetime import datetime
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import StudentTaskAnswer


class AnswerRepository:
    """Repository for student task answers and grading."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def save_answer(
        self,
        submission_id: int,
        question_id: int,
        student_id: int,
        school_id: int,
        answer_text: Optional[str] = None,
        selected_options: Optional[List[str]] = None
    ) -> StudentTaskAnswer:
        """Save an answer to a question."""
        result = await self.db.execute(
            select(StudentTaskAnswer).where(
                StudentTaskAnswer.submission_id == submission_id,
                StudentTaskAnswer.question_id == question_id
            )
        )
        answer = result.scalar_one_or_none()

        if answer:
            answer.answer_text = answer_text
            answer.selected_option_ids = selected_options
            answer.answered_at = datetime.utcnow()
        else:
            answer = StudentTaskAnswer(
                submission_id=submission_id,
                question_id=question_id,
                student_id=student_id,
                school_id=school_id,
                answer_text=answer_text,
                selected_option_ids=selected_options,
                answered_at=datetime.utcnow()
            )
            self.db.add(answer)

        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    async def get_answer_by_id(
        self,
        answer_id: int
    ) -> Optional[StudentTaskAnswer]:
        """Get answer by ID."""
        result = await self.db.execute(
            select(StudentTaskAnswer).where(
                StudentTaskAnswer.id == answer_id,
                StudentTaskAnswer.is_deleted == False
            )
        )
        return result.scalar_one_or_none()

    async def update_answer_grading(
        self,
        answer_id: int,
        is_correct: Optional[bool] = None,
        partial_score: Optional[float] = None,
        ai_score: Optional[float] = None,
        ai_confidence: Optional[float] = None,
        ai_feedback: Optional[str] = None,
        ai_rubric_scores: Optional[dict] = None,
        flagged_for_review: bool = False
    ) -> Optional[StudentTaskAnswer]:
        """Update answer with grading info."""
        answer = await self.get_answer_by_id(answer_id)
        if not answer:
            return None

        if is_correct is not None:
            answer.is_correct = is_correct
        if partial_score is not None:
            answer.partial_score = partial_score
        if ai_score is not None:
            answer.ai_score = ai_score
            answer.ai_graded_at = datetime.utcnow()
        if ai_confidence is not None:
            answer.ai_confidence = ai_confidence
        if ai_feedback is not None:
            answer.ai_feedback = ai_feedback
        if ai_rubric_scores is not None:
            answer.ai_rubric_scores = ai_rubric_scores

        answer.flagged_for_review = flagged_for_review
        answer.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(answer)
        return answer

    async def get_answers_for_review(
        self,
        school_id: int,
        limit: int = 50
    ) -> List[StudentTaskAnswer]:
        """Get answers flagged for teacher review."""
        result = await self.db.execute(
            select(StudentTaskAnswer)
            .options(
                selectinload(StudentTaskAnswer.question),
                selectinload(StudentTaskAnswer.student)
            )
            .where(
                StudentTaskAnswer.school_id == school_id,
                StudentTaskAnswer.flagged_for_review == True,
                StudentTaskAnswer.teacher_override_score.is_(None),
                StudentTaskAnswer.is_deleted == False
            )
            .order_by(StudentTaskAnswer.answered_at)
            .limit(limit)
        )
        return list(result.unique().scalars().all())

    async def teacher_review_answer(
        self,
        answer_id: int,
        score: float,
        feedback: Optional[str] = None
    ) -> Optional[StudentTaskAnswer]:
        """Teacher reviews an answer."""
        answer = await self.get_answer_by_id(answer_id)
        if not answer:
            return None

        answer.teacher_override_score = score
        answer.teacher_comment = feedback
        answer.flagged_for_review = False
        answer.updated_at = datetime.utcnow()

        await self.db.flush()
        await self.db.refresh(answer)
        return answer
