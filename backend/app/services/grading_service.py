"""
Grading Service для автоматической проверки тестов.

Поддерживает 4 типа вопросов:
- SINGLE_CHOICE: одна правильная опция
- MULTIPLE_CHOICE: несколько правильных опций (all or nothing)
- TRUE_FALSE: True/False вопрос
- SHORT_ANSWER: требует manual grading (is_correct=None)
"""

import logging
from typing import Optional
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.test import Question, QuestionType, TestPurpose
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.repositories.test_attempt_repo import TestAttemptRepository

logger = logging.getLogger(__name__)


class GradingService:
    """Service for automatic test grading and scoring."""

    def __init__(self, db: AsyncSession):
        """
        Initialize GradingService.

        Args:
            db: AsyncSession for database operations
        """
        self.db = db
        self.attempt_repo = TestAttemptRepository(db)

    def calculate_question_score(
        self,
        question: Question,
        answer: TestAttemptAnswer
    ) -> tuple[Optional[bool], float]:
        """
        Calculate score for a single question.

        Args:
            question: Question instance with options
            answer: TestAttemptAnswer with student's response

        Returns:
            Tuple of (is_correct, points_earned)
            - is_correct: True/False for auto-graded questions, None for SHORT_ANSWER
            - points_earned: Points awarded (0.0 to question.points)

        Raises:
            ValueError: If question has no correct options (data error)
        """
        # Edge case: Student didn't answer
        if not answer.selected_option_ids and not answer.answer_text:
            return (False, 0.0)

        # SINGLE_CHOICE and TRUE_FALSE: Exactly 1 correct option selected
        if question.question_type in (QuestionType.SINGLE_CHOICE, QuestionType.TRUE_FALSE):
            correct_option_ids = [opt.id for opt in question.options if opt.is_correct]

            # Data validation
            if not correct_option_ids:
                raise ValueError(f"Question {question.id} has no correct options")

            selected_ids = answer.selected_option_ids or []
            is_correct = (
                len(selected_ids) == 1 and
                selected_ids[0] in correct_option_ids
            )
            points = question.points if is_correct else 0.0

            return (is_correct, points)

        # MULTIPLE_CHOICE: All correct options selected, no incorrect ones (all or nothing)
        elif question.question_type == QuestionType.MULTIPLE_CHOICE:
            selected_set = set(answer.selected_option_ids or [])
            correct_set = {opt.id for opt in question.options if opt.is_correct}

            # Data validation
            if not correct_set:
                raise ValueError(f"Question {question.id} has no correct options")

            is_correct = (selected_set == correct_set)
            points = question.points if is_correct else 0.0

            return (is_correct, points)

        # SHORT_ANSWER: Manual grading required
        elif question.question_type == QuestionType.SHORT_ANSWER:
            # is_correct=None indicates manual grading needed
            return (None, 0.0)

        else:
            raise ValueError(f"Unknown question type: {question.question_type}")

    def calculate_test_score(self, attempt: TestAttempt) -> dict:
        """
        Calculate total score for a test attempt.

        Args:
            attempt: TestAttempt with graded answers

        Returns:
            Dictionary with:
            - score: Decimal score (0.0 to 1.0)
            - points_earned: Total points earned
            - total_points: Total points possible
            - passed: Whether student passed (score >= passing_score)
        """
        # Calculate totals
        total_points = sum(q.points for q in attempt.test.questions)
        points_earned = sum(a.points_earned or 0.0 for a in attempt.answers)

        # Division by zero protection
        score = points_earned / total_points if total_points > 0 else 0.0

        return {
            "score": score,
            "points_earned": points_earned,
            "total_points": total_points,
            "passed": score >= attempt.test.passing_score
        }

    async def grade_attempt(
        self,
        attempt_id: int,
        student_id: int,
        school_id: int
    ) -> TestAttempt:
        """
        Grade a test attempt and update mastery if applicable.

        This is the main method for automatic grading. It:
        1. Validates attempt ownership and status
        2. Grades each answer
        3. Calculates total score
        4. Updates attempt status to COMPLETED
        5. Triggers mastery update for FORMATIVE/SUMMATIVE tests

        Args:
            attempt_id: Test attempt ID
            student_id: Student ID (for ownership check)
            school_id: School ID (for tenant isolation)

        Returns:
            Graded TestAttempt with updated scores

        Raises:
            HTTPException 404: Attempt not found
            HTTPException 403: Access denied
            HTTPException 400: Invalid status (not IN_PROGRESS)
        """
        logger.info(f"Starting grading for attempt {attempt_id}")

        # 1. Load attempt with eager loading (answers, questions, test)
        attempt = await self.attempt_repo.get_with_answers(attempt_id)

        if not attempt:
            raise HTTPException(404, "Test attempt not found")

        # 2. Validate ownership and tenant isolation
        if attempt.student_id != student_id:
            logger.warning(
                f"Access denied: student {student_id} tried to grade "
                f"attempt {attempt_id} owned by student {attempt.student_id}"
            )
            raise HTTPException(403, "Access denied")

        if attempt.school_id != school_id:
            logger.warning(
                f"Tenant isolation violation: school {school_id} tried to access "
                f"attempt {attempt_id} from school {attempt.school_id}"
            )
            raise HTTPException(403, "Access denied")

        # 3. Validate status
        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise HTTPException(
                400,
                f"Cannot grade attempt with status {attempt.status}. "
                "Only IN_PROGRESS attempts can be graded."
            )

        # 4. Grade each answer
        # Note: We don't use explicit transaction here because SQLAlchemy
        # async sessions automatically wrap operations in transactions
        for answer in attempt.answers:
            # Find the corresponding question
            question = next(
                (q for q in attempt.test.questions if q.id == answer.question_id),
                None
            )

            if not question:
                logger.error(
                    f"Question {answer.question_id} not found in test {attempt.test_id}"
                )
                raise HTTPException(
                    500,
                    f"Data integrity error: question {answer.question_id} not found"
                )

            # Calculate score for this answer
            try:
                is_correct, points_earned = self.calculate_question_score(question, answer)
                answer.is_correct = is_correct
                answer.points_earned = points_earned
            except ValueError as e:
                logger.error(f"Error grading question {question.id}: {str(e)}")
                raise HTTPException(500, f"Grading error: {str(e)}")

        # 5. Calculate total score
        scores = self.calculate_test_score(attempt)

        # 6. Update attempt
        attempt.status = AttemptStatus.COMPLETED
        attempt.score = scores["score"]
        attempt.points_earned = scores["points_earned"]
        attempt.total_points = scores["total_points"]
        attempt.passed = scores["passed"]
        attempt.completed_at = datetime.now(timezone.utc)
        attempt.time_spent = int((attempt.completed_at - attempt.started_at).total_seconds())

        # 7. Save to database
        await self.db.commit()
        await self.db.refresh(attempt)

        logger.info(
            f"Completed grading for attempt {attempt_id}: "
            f"score={attempt.score:.2f}, passed={attempt.passed}"
        )

        # 8. Trigger mastery update (CRITICAL: Only for FORMATIVE and SUMMATIVE tests!)
        if attempt.test.test_purpose in (TestPurpose.FORMATIVE, TestPurpose.SUMMATIVE):
            from app.services.mastery_service import MasteryService
            mastery_service = MasteryService(self.db)

            # 8a. Update paragraph mastery (if test has paragraph_id)
            if attempt.test.paragraph_id:
                await mastery_service.update_paragraph_mastery(
                    student_id=attempt.student_id,
                    paragraph_id=attempt.test.paragraph_id,
                    test_score=attempt.score,
                    test_attempt_id=attempt.id,
                    school_id=attempt.school_id
                )
                logger.info(
                    f"Updated paragraph mastery for student {student_id}, "
                    f"paragraph {attempt.test.paragraph_id}"
                )
            else:
                logger.info(
                    f"Skipping paragraph mastery update: test {attempt.test_id} "
                    "has no paragraph_id (chapter-level test)"
                )

            # 8b. Trigger chapter mastery recalculation (ALWAYS if chapter_id exists)
            # This is called for BOTH paragraph-level and chapter-level tests
            if attempt.test.chapter_id:
                await mastery_service.trigger_chapter_recalculation(
                    student_id=attempt.student_id,
                    chapter_id=attempt.test.chapter_id,
                    school_id=attempt.school_id,
                    test_attempt=attempt
                )
                logger.info(
                    f"Triggered chapter mastery recalculation for student {student_id}, "
                    f"chapter {attempt.test.chapter_id}"
                )
            else:
                logger.info(
                    f"Skipping chapter mastery recalculation: test {attempt.test_id} "
                    "has no chapter_id"
                )
        else:
            logger.info(
                f"Skipping mastery update: test purpose is {attempt.test.test_purpose} "
                "(only FORMATIVE and SUMMATIVE affect mastery)"
            )

        return attempt
