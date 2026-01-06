"""
AI Answer Grading Service.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import HomeworkTaskQuestion
from app.services.homework.ai.utils.json_parser import parse_json_object
from app.services.homework.ai.utils.logging import log_ai_operation
from app.services.homework.ai.utils.prompt_builder import (
    build_grading_prompt,
    get_grading_system_prompt,
)
from app.services.llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)


@dataclass
class AIGradingResult:
    """Result of AI grading."""
    score: float  # 0.0 to 1.0
    confidence: float  # 0.0 to 1.0
    feedback: str
    rubric_scores: Optional[List[Dict[str, Any]]] = None
    strengths: List[str] = field(default_factory=list)
    improvements: List[str] = field(default_factory=list)


class AnswerGradingService:
    """Service for AI-powered answer grading."""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None
    ):
        self.db = db
        self.llm = llm_service or LLMService()

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
            student_id: Student ID (for logging)

        Returns:
            AIGradingResult with score and feedback
        """
        # Build grading prompt
        prompt = build_grading_prompt(question, answer_text)

        # Call LLM
        start_time = datetime.utcnow()
        try:
            response = await self.llm.generate(
                messages=[
                    {"role": "system", "content": get_grading_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=1000
            )
        except LLMServiceError as e:
            logger.error(f"LLM grading failed: {e}")
            return AIGradingResult(
                score=0.5,
                confidence=0.0,
                feedback="Не удалось оценить ответ автоматически. Требуется проверка учителем."
            )

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Parse grading result
        try:
            result = self._parse_grading_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse grading response: {e}")
            result = AIGradingResult(
                score=0.5,
                confidence=0.0,
                feedback="Ошибка обработки. Требуется проверка учителем."
            )

        # Log operation
        await log_ai_operation(
            db=self.db,
            operation_type="answer_grading",
            input_context={
                "question_id": question.id,
                "student_id": student_id,
                "answer_length": len(answer_text)
            },
            prompt_used=prompt,
            parsed_output={"score": result.score, "confidence": result.confidence},
            model_used=response.model,
            tokens_used=response.tokens_used or 0,
            latency_ms=latency_ms,
            success=result.confidence > 0
        )

        return result

    def _parse_grading_response(self, response: str) -> AIGradingResult:
        """Parse grading response from LLM."""
        data = parse_json_object(response)

        # Validate and normalize
        score = float(data.get("score", 0.5))
        score = max(0.0, min(1.0, score))

        confidence = float(data.get("confidence", 0.5))
        confidence = max(0.0, min(1.0, confidence))

        return AIGradingResult(
            score=score,
            confidence=confidence,
            feedback=data.get("feedback", ""),
            rubric_scores=data.get("rubric_scores"),
            strengths=data.get("strengths", []),
            improvements=data.get("improvements", [])
        )
