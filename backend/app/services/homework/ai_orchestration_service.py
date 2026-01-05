"""
AI Orchestration Service for Homework.

Handles:
- Coordinating AI question generation
- Managing regeneration workflows
"""
import logging
from typing import List, TYPE_CHECKING

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import HomeworkTaskQuestion, HomeworkStatus
from app.repositories.homework import HomeworkRepository
from app.schemas.homework import GenerationParams

if TYPE_CHECKING:
    from app.services.homework_ai_service import HomeworkAIService

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
        regenerate: bool = False
    ) -> List[HomeworkTaskQuestion]:
        """
        Generate questions for task using AI.

        Args:
            task_id: Task ID
            school_id: School ID
            regenerate: If True, deactivate existing and generate new

        Returns:
            List of generated questions

        Raises:
            AIOrchestrationError: If AI service not available or task misconfigured
        """
        if not self.ai_service:
            raise AIOrchestrationError("AI service not configured")

        task = await self.repo.get_task_by_id(task_id, school_id, load_questions=True)
        if not task:
            raise AIOrchestrationError("Task not found")

        if not task.generation_params:
            raise AIOrchestrationError(
                "Task has no generation parameters configured"
            )

        if task.questions and not regenerate:
            raise AIOrchestrationError(
                "Task already has questions. Use regenerate=True"
            )

        # Deactivate existing questions if regenerating
        if regenerate and task.questions:
            await self.repo.deactivate_task_questions(task_id)

        logger.info(
            f"Generating questions for task {task_id} with params: "
            f"{task.generation_params}"
        )

        # Generate via AI service
        params = GenerationParams.model_validate(task.generation_params)
        questions = await self.ai_service.generate_questions(
            paragraph_id=task.paragraph_id,
            params=params,
            task_id=task_id
        )

        # Save generated questions
        saved = []
        for q_data in questions:
            question = await self.repo.add_question(task_id, q_data)
            saved.append(question)

        # Mark task as AI-generated
        await self.repo.update_task(
            task_id=task_id,
            school_id=school_id,
            data={"ai_generated": True}
        )

        return saved
