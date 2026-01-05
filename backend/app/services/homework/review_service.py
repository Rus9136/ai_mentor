"""
Teacher Review Service.

Handles:
- Getting answers for review
- Teacher reviewing and grading answers
"""
from typing import Optional, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import StudentTaskAnswer
from app.repositories.homework import HomeworkRepository


class ReviewService:
    """Service for teacher review of student answers."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = HomeworkRepository(db)

    async def get_answers_for_review(
        self,
        school_id: int,
        homework_id: Optional[int] = None,
        limit: int = 50
    ) -> List[StudentTaskAnswer]:
        """
        Get answers needing teacher review.

        Args:
            school_id: School ID
            homework_id: Optional filter by homework
            limit: Max results

        Returns:
            List of answers flagged for review
        """
        return await self.repo.get_answers_for_review(
            school_id=school_id,
            limit=limit
        )

    async def review_answer(
        self,
        answer_id: int,
        teacher_id: int,
        score: float,
        feedback: Optional[str] = None
    ) -> StudentTaskAnswer:
        """
        Teacher reviews and grades an answer.

        Args:
            answer_id: Answer ID
            teacher_id: Teacher ID
            score: Score (0.0 to 1.0)
            feedback: Optional feedback

        Returns:
            Updated answer
        """
        return await self.repo.teacher_review_answer(
            answer_id=answer_id,
            score=score,
            feedback=feedback
        )
