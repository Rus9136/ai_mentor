"""
Homework AI Service for question generation and answer grading.

Uses LLM (Cerebras/OpenRouter) for:
- Generating questions from paragraph content
- Grading open-ended answers
- Personalization based on student mastery
"""
import json
import logging
import re
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import (
    HomeworkTaskQuestion,
    AIGenerationLog,
)
from app.services.llm_service import LLMService, LLMServiceError
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.homework import HomeworkRepository
from app.schemas.homework import GenerationParams, BloomLevel

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


class HomeworkAIServiceError(Exception):
    """Exception for AI service errors."""
    pass


class HomeworkAIService:
    """
    AI Service for homework question generation and grading.

    Uses Cerebras/OpenRouter LLM for fast, cost-effective AI operations.
    All operations are logged to AIGenerationLog table for analytics.
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
        self.llm = llm_service or LLMService()
        self.paragraph_repo = ParagraphRepository(db)
        self.homework_repo = HomeworkRepository(db)

    # =========================================================================
    # Question Generation
    # =========================================================================

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
            HomeworkAIServiceError: If generation fails
        """
        # 1. Get paragraph content
        paragraph = await self.paragraph_repo.get_by_id(paragraph_id)
        if not paragraph:
            raise HomeworkAIServiceError(f"Paragraph {paragraph_id} not found")

        # Get content text (from content items)
        content = await self._get_paragraph_text(paragraph_id)
        if not content:
            raise HomeworkAIServiceError(
                f"Paragraph {paragraph_id} has no content"
            )

        # 2. Build prompt
        prompt = self._build_generation_prompt(content, params)

        # 3. Call LLM
        start_time = datetime.utcnow()
        try:
            response = await self.llm.generate(
                messages=[
                    {"role": "system", "content": self._get_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=3000
            )
        except LLMServiceError as e:
            logger.error(f"LLM generation failed: {e}")
            raise HomeworkAIServiceError(f"AI generation failed: {e}")

        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # 4. Parse response
        try:
            questions = self._parse_questions_response(response.content)
        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            # Log the error
            await self._log_operation(
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
            raise HomeworkAIServiceError(f"Failed to parse AI response: {e}")

        # 5. Log successful operation
        await self._log_operation(
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
        """
        Get text content from paragraph.

        Extracts text from paragraph_contents and concatenates.
        """
        from app.repositories.paragraph_content_repo import ParagraphContentRepository
        content_repo = ParagraphContentRepository(self.db)

        contents = await content_repo.get_all_by_paragraph(paragraph_id)

        texts = []
        for content in contents:
            if content.explain_text:
                texts.append(content.explain_text)

        return "\n\n".join(texts)

    def _get_system_prompt(self) -> str:
        """Get system prompt for question generation."""
        return """Ты — эксперт по созданию образовательных вопросов для школьников Казахстана.
Твоя задача — создавать качественные вопросы, которые проверяют понимание материала.

Требования к вопросам:
1. Вопросы должны быть на том же языке, что и контент
2. Для choice вопросов: всегда 4 варианта, один правильный
3. Для open_ended: добавляй критерии оценки (rubric)
4. Следуй таксономии Блума для указанных уровней
5. Вопросы должны быть практичными и полезными

ВАЖНО: Отвечай ТОЛЬКО валидным JSON массивом без дополнительного текста."""

    def _build_generation_prompt(
        self,
        content: str,
        params: GenerationParams
    ) -> str:
        """Build generation prompt."""
        # Truncate content if too long
        max_content_length = 4000
        if len(content) > max_content_length:
            content = content[:max_content_length] + "...\n[контент сокращён]"

        bloom_descriptions = {
            "remember": "запоминание фактов",
            "understand": "понимание концепций",
            "apply": "применение знаний",
            "analyze": "анализ и сравнение",
            "evaluate": "оценка и критика",
            "create": "создание нового"
        }

        bloom_str = ", ".join(
            f"{b} ({bloom_descriptions.get(b, b)})"
            for b in params.bloom_levels
        )

        return f"""## Контент параграфа:
{content}

## Задание:
Создай {params.questions_count} вопросов на основе контента выше.

## Требования:
- Типы вопросов: {", ".join(params.question_types)}
- Когнитивные уровни (Bloom): {bloom_str}
- Язык: {params.language}
- Каждый вопрос должен проверять понимание материала

## Формат ответа (JSON массив):
```json
[
  {{
    "question_text": "Текст вопроса...",
    "question_type": "single_choice",
    "options": [
      {{"id": "a", "text": "Вариант A", "is_correct": false}},
      {{"id": "b", "text": "Вариант B", "is_correct": true}},
      {{"id": "c", "text": "Вариант C", "is_correct": false}},
      {{"id": "d", "text": "Вариант D", "is_correct": false}}
    ],
    "correct_answer": null,
    "bloom_level": "understand",
    "points": 1,
    "grading_rubric": null
  }},
  {{
    "question_text": "Объясните...",
    "question_type": "open_ended",
    "options": null,
    "correct_answer": null,
    "bloom_level": "analyze",
    "points": 3,
    "grading_rubric": {{
      "criteria": [
        {{"name": "Полнота ответа", "max_score": 10, "description": "..."}},
        {{"name": "Аргументация", "max_score": 10, "description": "..."}}
      ],
      "max_total_score": 20
    }}
  }}
]
```

Верни ТОЛЬКО JSON массив вопросов."""

    def _parse_questions_response(self, response: str) -> List[Dict[str, Any]]:
        """Parse LLM response into question dicts."""
        # Try to extract JSON from response
        response = response.strip()

        # Remove markdown code blocks if present
        if response.startswith("```"):
            # Find the end of code block
            lines = response.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            response = "\n".join(json_lines)

        # Try to parse as JSON
        try:
            questions = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON array in response
            match = re.search(r'\[[\s\S]*\]', response)
            if match:
                questions = json.loads(match.group())
            else:
                raise ValueError("Could not find JSON array in response")

        if not isinstance(questions, list):
            raise ValueError("Response is not a JSON array")

        # Validate and normalize questions
        validated = []
        for i, q in enumerate(questions):
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
        """Validate and normalize a question dict."""
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

    # =========================================================================
    # Answer Grading
    # =========================================================================

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
        prompt = self._build_grading_prompt(question, answer_text)

        # Call LLM
        start_time = datetime.utcnow()
        try:
            response = await self.llm.generate(
                messages=[
                    {"role": "system", "content": self._get_grading_system_prompt()},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,  # Lower temperature for consistency
                max_tokens=1000
            )
        except LLMServiceError as e:
            logger.error(f"LLM grading failed: {e}")
            # Return uncertain result
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
        await self._log_operation(
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

    def _get_grading_system_prompt(self) -> str:
        """Get system prompt for grading."""
        return """Ты — учитель, оценивающий ответы учеников.
Твоя задача — объективно оценить ответ и дать конструктивную обратную связь.

Принципы оценки:
1. Оценивай содержание, а не стиль изложения
2. Учитывай частичную правильность
3. Feedback должен быть позитивным и помогать ученику
4. Если не уверен в оценке — ставь низкую confidence

ВАЖНО: Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""

    def _build_grading_prompt(
        self,
        question: HomeworkTaskQuestion,
        answer: str
    ) -> str:
        """Build grading prompt."""
        rubric_text = ""
        if question.grading_rubric:
            rubric_text = f"""
## Критерии оценки (rubric):
```json
{json.dumps(question.grading_rubric, ensure_ascii=False, indent=2)}
```
"""

        return f"""## Вопрос:
{question.question_text}

## Ответ ученика:
{answer}
{rubric_text}
## Задание:
Оцени ответ ученика.

## Формат ответа (JSON):
```json
{{
  "score": 0.75,
  "confidence": 0.85,
  "feedback": "Хороший ответ. Ты правильно объяснил... Можно было бы добавить...",
  "rubric_scores": [
    {{"name": "Критерий 1", "score": 8, "max_score": 10, "comment": "..."}}
  ],
  "strengths": ["Что сделано хорошо"],
  "improvements": ["Что можно улучшить"]
}}
```

Где:
- score: 0.0 - 1.0 (доля от максимального балла)
- confidence: 0.0 - 1.0 (уверенность в оценке, <0.7 = нужна проверка учителя)
- feedback: конструктивный комментарий для ученика

Верни ТОЛЬКО JSON."""

    def _parse_grading_response(self, response: str) -> AIGradingResult:
        """Parse grading response from LLM."""
        response = response.strip()

        # Remove markdown code blocks
        if response.startswith("```"):
            lines = response.split("\n")
            json_lines = []
            in_block = False
            for line in lines:
                if line.startswith("```"):
                    in_block = not in_block
                    continue
                if in_block:
                    json_lines.append(line)
            response = "\n".join(json_lines)

        # Parse JSON
        try:
            data = json.loads(response)
        except json.JSONDecodeError:
            # Try to find JSON object
            match = re.search(r'\{[\s\S]*\}', response)
            if match:
                data = json.loads(match.group())
            else:
                raise ValueError("Could not find JSON in response")

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

    # =========================================================================
    # Personalization
    # =========================================================================

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
        from app.services.mastery_service import MasteryService
        mastery_service = MasteryService(self.db)

        # Get student's mastery level
        mastery = await mastery_service.paragraph_repo.get_by_student_paragraph(
            student_id=student_id,
            paragraph_id=paragraph_id
        )

        params = base_params.model_copy()

        if mastery:
            if mastery.status == "mastered":
                # High level - harder questions
                params.bloom_levels = [
                    BloomLevel.ANALYZE,
                    BloomLevel.EVALUATE,
                    BloomLevel.CREATE
                ]
                params.questions_count = max(3, params.questions_count - 2)

            elif mastery.status == "progressing":
                # Medium level - standard
                params.bloom_levels = [
                    BloomLevel.UNDERSTAND,
                    BloomLevel.APPLY,
                    BloomLevel.ANALYZE
                ]

            else:  # struggling
                # Low level - easier questions
                params.bloom_levels = [
                    BloomLevel.REMEMBER,
                    BloomLevel.UNDERSTAND,
                    BloomLevel.APPLY
                ]
                params.questions_count = min(7, params.questions_count + 2)

        return params

    # =========================================================================
    # Logging
    # =========================================================================

    async def _log_operation(
        self,
        operation_type: str,
        input_context: Dict[str, Any],
        prompt_used: str,
        parsed_output: Dict[str, Any],
        model_used: str,
        tokens_used: int,
        latency_ms: float,
        success: bool = True,
        task_id: Optional[int] = None,
        answer_id: Optional[int] = None
    ):
        """Log AI operation for analytics."""
        log = AIGenerationLog(
            operation_type=operation_type,
            input_context=input_context,
            prompt_used=prompt_used[:10000],  # Truncate if too long
            parsed_output=parsed_output,
            model_used=model_used,
            tokens_input=tokens_used // 2,  # Approximate split
            tokens_output=tokens_used // 2,
            latency_ms=int(latency_ms),
            success=success,
            homework_task_id=task_id
        )
        self.db.add(log)
        await self.db.flush()
