"""
AI Orchestration Service for Homework.

Handles:
- Coordinating AI question generation
- Managing regeneration workflows
"""
import logging
from typing import List, Optional, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import HomeworkTaskQuestion, HomeworkStatus
from app.repositories.homework import HomeworkRepository
from app.schemas.homework import GenerationParams

if TYPE_CHECKING:
    from app.services.homework.ai import HomeworkAIService

logger = logging.getLogger(__name__)


class AIOrchestrationError(Exception):
    """Exception for AI orchestration errors."""
    pass


class AIOrchestrationService:
    """Service for orchestrating AI operations on homework."""

    def __init__(
        self,
        db: AsyncSession,
        ai_service: "HomeworkAIService"
    ):
        self.db = db
        self.repo = HomeworkRepository(db)
        self.ai_service = ai_service

    async def generate_questions_for_task(
        self,
        task_id: int,
        school_id: int,
        regenerate: bool = False,
        params: Optional[GenerationParams] = None
    ) -> List[HomeworkTaskQuestion]:
        """
        Generate questions for task using AI.

        Args:
            task_id: Task ID
            school_id: School ID
            regenerate: If True, deactivate existing and generate new
            params: Generation parameters (if None, uses task.generation_params or defaults)

        Returns:
            List of generated questions

        Raises:
            AIOrchestrationError: If AI service not available or task misconfigured
        """
        if not self.ai_service:
            raise AIOrchestrationError(
                "Сервис AI не настроен. Обратитесь к администратору."
            )

        task = await self.repo.get_task_by_id(task_id, school_id, load_questions=True)
        if not task:
            raise AIOrchestrationError(
                "Задание не найдено. Возможно, оно было удалено."
            )

        # Determine generation params: passed > from task > defaults
        if params:
            generation_params = params
        elif task.generation_params:
            generation_params = GenerationParams.model_validate(task.generation_params)
        else:
            generation_params = GenerationParams()

        if task.questions and not regenerate:
            raise AIOrchestrationError(
                "Вопросы уже сгенерированы. Для повторной генерации включите режим перегенерации."
            )

        # Deactivate existing questions if regenerating
        if regenerate and task.questions:
            await self.repo.deactivate_task_questions(task_id)

        logger.info(
            f"Generating questions for task {task_id} "
            f"(type={task.task_type.value}) with params: "
            f"{generation_params.model_dump()}"
        )

        # Generate via AI service with task type for type-specific prompts
        questions = await self.ai_service.generate_questions(
            paragraph_id=task.paragraph_id,
            params=generation_params,
            task_id=task_id,
            task_type=task.task_type
        )

        # Save generated questions
        saved = []
        for q_data in questions:
            question = await self.repo.add_question(task_id, school_id, q_data)
            saved.append(question)

        # Mark task as AI-generated
        await self.repo.update_task(
            task_id=task_id,
            school_id=school_id,
            data={"ai_generated": True}
        )

        return saved
