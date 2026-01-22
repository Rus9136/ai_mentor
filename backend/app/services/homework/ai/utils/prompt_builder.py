"""
Prompt building utilities for AI operations.

Provides type-specific prompt builders for different homework task types:
- READ: Reading comprehension check questions
- QUIZ: Test questions (single/multiple choice)
- OPEN_QUESTION: Open-ended questions with grading rubrics
- ESSAY: Essay topics with evaluation criteria
- PRACTICE: Practical tasks and case studies
- CODE: Programming tasks with test cases
"""

import json
from typing import TYPE_CHECKING, Optional

from app.schemas.homework import GenerationParams

if TYPE_CHECKING:
    from app.models.homework import HomeworkTaskQuestion, HomeworkTaskType
    from app.repositories.paragraph_repo import ContentMetadata


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


def build_generation_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for question generation.

    Args:
        content: Paragraph text content
        params: Generation parameters
        metadata: Content metadata (subject, chapter, paragraph info)

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

    # Build context section if metadata available
    context_section = ""
    if metadata:
        context_section = f"""## Контекст материала:
- Предмет: {metadata['subject']}
- Класс: {metadata['grade_level']}
- Учебник: {metadata['textbook_title']}
- Глава {metadata['chapter_number']}: {metadata['chapter_title']}
- Параграф §{metadata['paragraph_number']}: {metadata.get('paragraph_title') or 'Без названия'}

"""

    # Difficulty hint based on grade level
    difficulty_hint = ""
    if metadata:
        grade = metadata['grade_level']
        if grade <= 7:
            difficulty_hint = "- Сложность: адаптируй для младших классов (7 класс и ниже), используй простые формулировки\n"
        elif grade <= 9:
            difficulty_hint = "- Сложность: средний уровень для 8-9 классов\n"
        else:
            difficulty_hint = "- Сложность: продвинутый уровень для 10-11 классов\n"

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Создай {params.questions_count} вопросов на основе контента выше.

## Требования:
- Типы вопросов: {", ".join(params.question_types)}
- Когнитивные уровни (Bloom): {bloom_str}
- Язык: {params.language}
{difficulty_hint}- Каждый вопрос должен проверять понимание материала
- Вопросы должны соответствовать предмету и уровню класса

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


# =============================================================================
# Type-Specific Prompt Builders
# =============================================================================

def _build_context_section(metadata: Optional["ContentMetadata"]) -> str:
    """Build context section from metadata."""
    if not metadata:
        return ""
    return f"""## Контекст материала:
- Предмет: {metadata['subject']}
- Класс: {metadata['grade_level']}
- Учебник: {metadata['textbook_title']}
- Глава {metadata['chapter_number']}: {metadata['chapter_title']}
- Параграф §{metadata['paragraph_number']}: {metadata.get('paragraph_title') or 'Без названия'}

"""


def _get_difficulty_hint(metadata: Optional["ContentMetadata"]) -> str:
    """Get difficulty hint based on grade level."""
    if not metadata:
        return ""
    grade = metadata['grade_level']
    if grade <= 7:
        return "- Сложность: адаптируй для младших классов (7 класс и ниже), используй простые формулировки\n"
    elif grade <= 9:
        return "- Сложность: средний уровень для 8-9 классов\n"
    else:
        return "- Сложность: продвинутый уровень для 10-11 классов\n"


def _truncate_content(content: str, max_length: int = 4000) -> str:
    """Truncate content if too long."""
    if len(content) > max_length:
        return content[:max_length] + "...\n[контент сокращён]"
    return content


def build_reading_check_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for READ task type - simple comprehension check questions.

    Generates 2-3 simple questions to verify the student read and understood
    the basic ideas of the material.
    """
    content = _truncate_content(content)
    context_section = _build_context_section(metadata)
    difficulty_hint = _get_difficulty_hint(metadata)

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Создай 2-3 простых вопроса для самопроверки после прочтения.

## Требования:
- Вопросы должны проверять, что ученик прочитал и понял основные идеи
- Типы вопросов: ТОЛЬКО true_false или single_choice
- Когнитивные уровни: remember (запоминание), understand (понимание)
- Язык: {params.language}
{difficulty_hint}- НЕ требуются сложные вопросы — только базовая проверка понимания
- Каждый вопрос должен иметь 4 варианта ответа для single_choice

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
    "bloom_level": "remember",
    "points": 1,
    "grading_rubric": null
  }}
]
```

Верни ТОЛЬКО JSON массив с 2-3 вопросами."""


def build_quiz_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for QUIZ task type - test questions with multiple choice.

    This is the default generation type with full parameter support.
    """
    content = _truncate_content(content)
    context_section = _build_context_section(metadata)
    difficulty_hint = _get_difficulty_hint(metadata)

    bloom_str = ", ".join(
        f"{b} ({BLOOM_DESCRIPTIONS.get(b, b)})"
        for b in params.bloom_levels
    )

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Создай {params.questions_count} тестовых вопросов для проверки знаний.

## Требования:
- Типы вопросов: {", ".join(params.question_types)}
- Когнитивные уровни (Bloom): {bloom_str}
- Язык: {params.language}
{difficulty_hint}- Каждый вопрос с 4 вариантами ответа (для choice типов)
- Вопросы должны быть чёткими и однозначными
- Дистракторы должны быть правдоподобными

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
  }}
]
```

Верни ТОЛЬКО JSON массив вопросов."""


def build_open_question_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for OPEN_QUESTION task type - open-ended questions with rubrics.

    Generates questions that require written answers with grading criteria.
    """
    content = _truncate_content(content)
    context_section = _build_context_section(metadata)
    difficulty_hint = _get_difficulty_hint(metadata)

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Создай {params.questions_count} открытых вопросов, требующих развёрнутого ответа.

## Требования:
- Вопросы должны требовать размышления и аргументации
- Когнитивные уровни: understand, apply, analyze, evaluate
- Язык: {params.language}
{difficulty_hint}- Для каждого вопроса добавь критерии оценки (grading_rubric)
- Вопросы должны проверять глубокое понимание материала

## Формат ответа (JSON массив):
```json
[
  {{
    "question_text": "Объясните, почему...",
    "question_type": "open_ended",
    "options": null,
    "correct_answer": null,
    "bloom_level": "analyze",
    "points": 5,
    "grading_rubric": {{
      "criteria": [
        {{"name": "Полнота ответа", "max_score": 2, "description": "Ученик раскрыл все ключевые аспекты"}},
        {{"name": "Аргументация", "max_score": 2, "description": "Ответ подкреплён примерами и фактами"}},
        {{"name": "Понимание материала", "max_score": 1, "description": "Демонстрирует понимание основных концепций"}}
      ],
      "max_total_score": 5
    }},
    "expected_answer_hints": "Ключевые пункты, которые должен упомянуть ученик..."
  }}
]
```

Верни ТОЛЬКО JSON массив вопросов."""


def build_essay_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for ESSAY task type - essay topic with evaluation criteria.

    Generates an essay topic, requirements, and grading rubric.
    """
    content = _truncate_content(content)
    context_section = _build_context_section(metadata)
    difficulty_hint = _get_difficulty_hint(metadata)

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Предложи тему для эссе на основе изученного материала.

## Требования:
- Тема должна быть интересной и побуждать к размышлению
- Язык: {params.language}
{difficulty_hint}- Включи детальные критерии оценки
- Укажи требования к объёму

## Формат ответа (JSON):
```json
[
  {{
    "question_text": "Напишите эссе на тему: [Тема эссе]",
    "question_type": "open_ended",
    "options": null,
    "correct_answer": null,
    "bloom_level": "create",
    "points": 20,
    "grading_rubric": {{
      "criteria": [
        {{"name": "Раскрытие темы", "max_score": 6, "description": "Тема полностью раскрыта, использованы факты из материала"}},
        {{"name": "Аргументация", "max_score": 6, "description": "Аргументы логичны и подкреплены примерами"}},
        {{"name": "Структура", "max_score": 4, "description": "Есть вступление, основная часть, заключение"}},
        {{"name": "Грамотность", "max_score": 4, "description": "Текст написан без грубых ошибок"}}
      ],
      "max_total_score": 20
    }},
    "essay_requirements": {{
      "min_words": 150,
      "max_words": 400,
      "required_elements": ["введение", "основная часть с аргументами", "заключение"]
    }},
    "expected_answer_hints": "Ключевые тезисы и факты, которые должны быть упомянуты..."
  }}
]
```

Верни ТОЛЬКО JSON массив с одной темой эссе."""


def build_practice_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for PRACTICE task type - practical tasks and case studies.

    Generates practical problems, cases, or situations for analysis.
    """
    content = _truncate_content(content)
    context_section = _build_context_section(metadata)
    difficulty_hint = _get_difficulty_hint(metadata)

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Создай {params.questions_count} практических задач на применение знаний.

## Требования:
- Задачи должны быть практическими: кейсы, ситуации, задачи
- Когнитивные уровни: apply (применение), analyze (анализ)
- Язык: {params.language}
{difficulty_hint}- Каждая задача должна иметь чёткие условия
- Добавь критерии оценки для каждой задачи

## Формат ответа (JSON массив):
```json
[
  {{
    "question_text": "Ситуация: [описание ситуации/кейса]\\n\\nЗадание: [что нужно сделать]",
    "question_type": "open_ended",
    "options": null,
    "correct_answer": null,
    "bloom_level": "apply",
    "points": 10,
    "grading_rubric": {{
      "criteria": [
        {{"name": "Понимание задачи", "max_score": 3, "description": "Ученик правильно понял условия задачи"}},
        {{"name": "Применение знаний", "max_score": 4, "description": "Применены соответствующие концепции из материала"}},
        {{"name": "Решение", "max_score": 3, "description": "Предложено корректное решение"}}
      ],
      "max_total_score": 10
    }},
    "hints": ["Подсказка 1", "Подсказка 2"],
    "expected_answer_hints": "Ключевые шаги решения..."
  }}
]
```

Верни ТОЛЬКО JSON массив практических задач."""


def build_code_prompt(
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Build prompt for CODE task type - programming tasks with test cases.

    Generates programming problems with examples, constraints, and tests.
    """
    content = _truncate_content(content)
    context_section = _build_context_section(metadata)
    difficulty_hint = _get_difficulty_hint(metadata)

    return f"""{context_section}## Контент параграфа:
{content}

## Задание:
Создай задачу по программированию на основе изученного материала.

## Требования:
- Задача должна проверять понимание алгоритмов или концепций из материала
- Язык условия: {params.language}
{difficulty_hint}- Включи примеры ввода-вывода
- Добавь тестовые случаи для проверки

## Формат ответа (JSON массив):
```json
[
  {{
    "question_text": "Напишите функцию/программу, которая [описание задачи]",
    "question_type": "code",
    "options": null,
    "correct_answer": null,
    "bloom_level": "apply",
    "points": 15,
    "code_task": {{
      "title": "Название задачи",
      "description": "Подробное описание задачи",
      "input_format": "Описание формата входных данных",
      "output_format": "Описание формата выходных данных",
      "examples": [
        {{
          "input": "пример входа",
          "output": "пример выхода",
          "explanation": "объяснение примера"
        }}
      ],
      "constraints": ["ограничение 1", "ограничение 2"],
      "test_cases": [
        {{"input": "тест 1", "expected_output": "результат 1"}},
        {{"input": "тест 2", "expected_output": "результат 2"}}
      ],
      "hints": ["подсказка 1"],
      "difficulty": "medium",
      "allowed_languages": ["python", "javascript"]
    }},
    "grading_rubric": {{
      "criteria": [
        {{"name": "Корректность", "max_score": 10, "description": "Программа проходит все тесты"}},
        {{"name": "Читаемость кода", "max_score": 3, "description": "Код понятен и хорошо структурирован"}},
        {{"name": "Эффективность", "max_score": 2, "description": "Решение оптимально по времени/памяти"}}
      ],
      "max_total_score": 15
    }}
  }}
]
```

Верни ТОЛЬКО JSON массив с задачей по программированию."""


def get_prompt_for_task_type(
    task_type: "HomeworkTaskType",
    content: str,
    params: GenerationParams,
    metadata: Optional["ContentMetadata"] = None
) -> str:
    """
    Router function - selects the appropriate prompt builder based on task type.

    Args:
        task_type: Type of homework task (READ, QUIZ, OPEN_QUESTION, etc.)
        content: Paragraph text content
        params: Generation parameters
        metadata: Content metadata (subject, chapter, paragraph info)

    Returns:
        Formatted prompt string for the specific task type
    """
    # Import here to avoid circular imports
    from app.models.homework import HomeworkTaskType

    # Map task types to prompt builders
    prompt_builders = {
        HomeworkTaskType.READ: build_reading_check_prompt,
        HomeworkTaskType.QUIZ: build_quiz_prompt,
        HomeworkTaskType.OPEN_QUESTION: build_open_question_prompt,
        HomeworkTaskType.ESSAY: build_essay_prompt,
        HomeworkTaskType.PRACTICE: build_practice_prompt,
        HomeworkTaskType.CODE: build_code_prompt,
    }

    # Get the appropriate builder, default to quiz if unknown
    builder = prompt_builders.get(task_type, build_quiz_prompt)

    return builder(content, params, metadata)


def get_system_prompt_for_task_type(task_type: "HomeworkTaskType") -> str:
    """
    Get type-specific system prompt.

    Args:
        task_type: Type of homework task

    Returns:
        System prompt string
    """
    # Import here to avoid circular imports
    from app.models.homework import HomeworkTaskType

    base_prompt = """Ты — эксперт по созданию образовательных материалов для школьников Казахстана.

Требования:
1. Контент должен быть на том же языке, что и исходный материал
2. Следуй таксономии Блума для указанных уровней
3. Материалы должны быть практичными и полезными
4. Учитывай возрастные особенности учеников

ВАЖНО: Отвечай ТОЛЬКО валидным JSON без дополнительного текста."""

    type_specific = {
        HomeworkTaskType.READ: """
Твоя задача — создавать простые вопросы для проверки прочтения материала.
Вопросы должны быть базовыми и проверять только то, что ученик прочитал текст.""",

        HomeworkTaskType.QUIZ: """
Твоя задача — создавать качественные тестовые вопросы.
Для choice вопросов: всегда 4 варианта, один или несколько правильных.
Дистракторы должны быть правдоподобными, но неверными.""",

        HomeworkTaskType.OPEN_QUESTION: """
Твоя задача — создавать открытые вопросы, требующие развёрнутого ответа.
Каждый вопрос должен иметь чёткие критерии оценки (rubric).
Вопросы должны проверять глубокое понимание, а не просто запоминание.""",

        HomeworkTaskType.ESSAY: """
Твоя задача — предлагать темы для эссе с детальными критериями оценки.
Темы должны быть интересными и побуждать к размышлению.
Включай требования к структуре и объёму.""",

        HomeworkTaskType.PRACTICE: """
Твоя задача — создавать практические задачи и кейсы.
Задачи должны применять знания из материала к реальным ситуациям.
Включай чёткие условия и критерии оценки.""",

        HomeworkTaskType.CODE: """
Твоя задача — создавать задачи по программированию.
Задачи должны быть связаны с изучаемым материалом.
Включай примеры, тестовые случаи и ограничения.""",
    }

    specific = type_specific.get(task_type, type_specific[HomeworkTaskType.QUIZ])

    return base_prompt + specific
