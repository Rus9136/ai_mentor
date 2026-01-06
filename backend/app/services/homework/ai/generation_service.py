"""
AI Question Generation Service.
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.paragraph_repo import ParagraphRepository
from app.schemas.homework import GenerationParams
from app.services.homework.ai.utils.json_parser import parse_json_array
from app.services.homework.ai.utils.logging import log_ai_operation
from app.services.homework.ai.utils.prompt_builder import (
    build_generation_prompt,
    get_generation_system_prompt,
)
from app.services.llm_service import LLMService, LLMServiceError

logger = logging.getLogger(__name__)


class QuestionGenerationError(Exception):
    """Exception for question generation errors."""
    pass


class QuestionGenerationService:
    """Service for AI-powered question generation."""

    def __init__(
        self,
        db: AsyncSession,
        llm_service: Optional[LLMService] = None
    ):
        self.db = db
        self.llm = llm_service or LLMService()
        self.paragraph_repo = ParagraphRepository(db)

    async def generate_questions(
        self,
        paragraph_id: int,
        params: GenerationParams,
        task_id: int
    ) -> List[Dict[str, Any]]:
        """
        Generate questions based on paragraph content.

        Args:
            paragraph_id: Source paragraph ID
            params: Generation parameters
            task_id: Task ID (for logging)

        Returns:
            List of question dicts ready for database insertion

        Raises:
            QuestionGenerationError: If generation fails
        """
        # 1. Get paragraph content
        paragraph = await self.paragraph_repo.get_by_id(paragraph_id)
        if not paragraph:
            raise QuestionGenerationError(f"Paragraph {paragraph_id} not found")

        content = await self._get_paragraph_text(paragraph_id)
        if not content:
            raise QuestionGenerationError(
                f"Paragraph {paragraph_id} has no content"
            )

        # 2. Build prompt
        prompt = build_generation_prompt(content, params)

        # 3. Call LLM
        start_time = datetime.utcnow()
        try:
            response = await self.llm.generate(
                messages=[
                    {"role": "system", "content": get_generation_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
        except LLMServiceError as e:
            logger.error(f"LLM generation failed: {e}")
            raise QuestionGenerationError(f"AI generation failed: {e}") from e

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # 4. Parse response
        try:
            raw_questions = parse_json_array(response.content)
            questions = self._validate_questions(raw_questions)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            await log_ai_operation(
                db=self.db,
                operation_type="question_generation",
                input_context={
                    "paragraph_id": paragraph_id,
                    "params": params.model_dump()
                },
                prompt_used=prompt,
                parsed_output={"error": str(e), "raw_response": response.content},
                model_used=response.model,
                tokens_used=response.tokens_used or 0,
                latency_ms=latency_ms,
                success=False,
                task_id=task_id
            )
            raise QuestionGenerationError(f"Failed to parse AI response: {e}") from e

        # 5. Log successful operation
        await log_ai_operation(
            db=self.db,
            operation_type="question_generation",
            input_context={
                "paragraph_id": paragraph_id,
                "params": params.model_dump()
            },
            prompt_used=prompt,
            parsed_output={"questions_count": len(questions)},
            model_used=response.model,
            tokens_used=response.tokens_used or 0,
            latency_ms=latency_ms,
            success=True,
            task_id=task_id
        )

        logger.info(
            f"Generated {len(questions)} questions for paragraph {paragraph_id}"
        )

        return questions

    async def _get_paragraph_text(self, paragraph_id: int) -> str:
        """Get text content from paragraph."""
        from app.repositories.paragraph_content_repo import ParagraphContentRepository
        content_repo = ParagraphContentRepository(self.db)

        contents = await content_repo.get_all_by_paragraph(paragraph_id)

        texts = []
        for content in contents:
            if content.explain_text:
                texts.append(content.explain_text)

        return "\n\n".join(texts)

    def _validate_questions(
        self,
        raw_questions: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Validate and normalize question dicts."""
        validated = []
        for i, q in enumerate(raw_questions):
            try:
                validated_q = self._validate_question(q, i)
                validated.append(validated_q)
            except ValueError as e:
                logger.warning(f"Skipping invalid question {i}: {e}")
                continue

        if not validated:
            raise ValueError("No valid questions in response")

        return validated

    def _validate_question(
        self,
        q: Dict[str, Any],
        index: int
    ) -> Dict[str, Any]:
        """Validate and normalize a single question dict."""
        # Required fields
        if "question_text" not in q or not q["question_text"]:
            raise ValueError(f"Question {index}: missing question_text")

        q_type = q.get("question_type", "single_choice")
        valid_types = [
            "single_choice", "multiple_choice", "short_answer",
            "open_ended", "true_false"
        ]
        if q_type not in valid_types:
            q_type = "single_choice"

        # Validate options for choice questions
        if q_type in ("single_choice", "multiple_choice", "true_false"):
            options = q.get("options", [])
            if not options or len(options) < 2:
                raise ValueError(
                    f"Question {index}: choice questions need at least 2 options"
                )
            # Ensure at least one correct option
            has_correct = any(opt.get("is_correct") for opt in options)
            if not has_correct:
                options[0]["is_correct"] = True

        # Normalize bloom level
        bloom = q.get("bloom_level", "understand")
        valid_blooms = [
            "remember", "understand", "apply",
            "analyze", "evaluate", "create"
        ]
        if bloom not in valid_blooms:
            bloom = "understand"

        return {
            "question_text": q["question_text"].strip(),
            "question_type": q_type,
            "options": q.get("options"),
            "correct_answer": q.get("correct_answer"),
            "bloom_level": bloom,
            "points": max(1, min(10, q.get("points") or 1)),
            "grading_rubric": q.get("grading_rubric"),
        }
