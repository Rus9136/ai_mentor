"""
Homework AI services package.

Provides modular AI services for question generation and grading.
Supports different generation strategies for different task types.
"""

from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import HomeworkTaskQuestion, HomeworkTaskType
from app.schemas.homework import GenerationParams
from app.services.homework.ai.generation_service import (
    QuestionGenerationError,
    QuestionGenerationService,
)
from app.services.homework.ai.grading_ai_service import (
    AIGradingResult,
    AnswerGradingService,
)
from app.services.homework.ai.personalization_service import PersonalizationService
from app.services.llm_service import LLMService


class HomeworkAIServiceError(Exception):
    """Exception for AI service errors."""
    pass


class HomeworkAIService:
    """
    Facade for homework AI operations.

    Provides unified interface while delegating to specialized services.
    """

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None
    ):
        """
        Initialize HomeworkAIService.

        Args:
            db: AsyncSession for database operations
            llm_service: Optional LLM service (creates default if None)
        """
        self.db = db
        self._generation = QuestionGenerationService(db, llm_service)
        self._grading = AnswerGradingService(db, llm_service)
        self._personalization = PersonalizationService(db)

    async def generate_questions(
        self,
        paragraph_id: int,
        params: GenerationParams,
        task_id: int,
        task_type: HomeworkTaskType = HomeworkTaskType.QUIZ
    ) -> List[Dict[str, Any]]:
        """
        Generate questions based on paragraph content and task type.

        Args:
            paragraph_id: Source paragraph ID
            params: Generation parameters
            task_id: Task ID (for logging)
            task_type: Type of homework task (determines generation strategy)

        Returns:
            List of question dicts

        Raises:
            HomeworkAIServiceError: If generation fails
        """
        try:
            return await self._generation.generate_questions(
                paragraph_id, params, task_id, task_type
            )
        except QuestionGenerationError as e:
            raise HomeworkAIServiceError(str(e)) from e

    async def grade_answer(
        self,
        question: HomeworkTaskQuestion,
        answer_text: str,
        student_id: int
    ) -> AIGradingResult:
        """
        Grade an open-ended answer using AI.

        Args:
            question: Question being answered
            answer_text: Student's answer
            student_id: Student ID

        Returns:
            AIGradingResult with score and feedback
        """
        return await self._grading.grade_answer(question, answer_text, student_id)

    async def personalize_difficulty(
        self,
        student_id: int,
        paragraph_id: int,
        base_params: GenerationParams
    ) -> GenerationParams:
        """
        Adapt difficulty based on student mastery.

        Args:
            student_id: Student ID
            paragraph_id: Paragraph ID
            base_params: Base generation parameters

        Returns:
            Adjusted GenerationParams
        """
        return await self._personalization.personalize_difficulty(
            student_id, paragraph_id, base_params
        )


__all__ = [
    "HomeworkAIService",
    "HomeworkAIServiceError",
    "AIGradingResult",
    # Direct access to specialized services
    "QuestionGenerationService",
    "QuestionGenerationError",
    "AnswerGradingService",
    "PersonalizationService",
]
