"""
Prompt building utilities for AI operations.
"""

import json
from typing import TYPE_CHECKING

from app.schemas.homework import GenerationParams

if TYPE_CHECKING:
    from app.models.homework import HomeworkTaskQuestion


BLOOM_DESCRIPTIONS = {
    "remember": "запоминание фактов",
    "understand": "понимание концепций",
    "apply": "применение знаний",
    "analyze": "анализ и сравнение",
    "evaluate": "оценка и критика",
    "create": "создание нового"
}


def get_generation_system_prompt() -> str:
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


def build_generation_prompt(content: str, params: GenerationParams) -> str:
    """
    Build prompt for question generation.

    Args:
        content: Paragraph text content
        params: Generation parameters

    Returns:
        Formatted prompt string
    """
    # Truncate content if too long
    max_content_length = 4000
    if len(content) > max_content_length:
        content = content[:max_content_length] + "...\n[контент сокращён]"

    bloom_str = ", ".join(
        f"{b} ({BLOOM_DESCRIPTIONS.get(b, b)})"
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


def get_grading_system_prompt() -> str:
    """Get system prompt for answer grading."""
    return """Ты — учитель, оценивающий ответы учеников.
Твоя задача — объективно оценить ответ и дать конструктивную обратную связь.

Принципы оценки:
1. Оценивай содержание, а не стиль изложения
2. Учитывай частичную правильность
3. Feedback должен быть позитивным и помогать ученику
4. Если не уверен в оценке — ставь низкую confidence

ВАЖНО: Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""


def build_grading_prompt(question: "HomeworkTaskQuestion", answer: str) -> str:
    """
    Build prompt for answer grading.

    Args:
        question: Question being answered
        answer: Student's answer text

    Returns:
        Formatted prompt string
    """
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
