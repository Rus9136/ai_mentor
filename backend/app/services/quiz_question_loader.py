"""
Quiz question loader: test loading, question shuffling, answer checking.
Extracted from quiz_service.py for reuse across quiz modules.
"""
import random
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test import Test, Question, QuestionOption, QuestionType
from app.schemas.quiz import QuizQuestionOut

# Question types allowed in quiz sessions
ALLOWED_QUESTION_TYPES = {QuestionType.SINGLE_CHOICE, QuestionType.SHORT_ANSWER}


async def load_test(db: AsyncSession, test_id: int) -> Optional[Test]:
    """Load test with eager-loaded questions and options."""
    result = await db.execute(
        select(Test)
        .options(selectinload(Test.questions).selectinload(Question.options))
        .where(Test.id == test_id)
    )
    return result.scalar_one_or_none()


def get_sorted_questions(test: Test) -> list[Question]:
    """Get active quiz-eligible questions sorted by sort_order."""
    return sorted(
        [q for q in test.questions if q.question_type in ALLOWED_QUESTION_TYPES and not q.is_deleted],
        key=lambda q: q.sort_order,
    )


def get_question_at_index(
    questions: list[Question], question_index: int, settings: dict, session_id: int,
) -> Optional[Question]:
    """Get question at logical index, applying question shuffle if enabled."""
    if question_index >= len(questions):
        return None
    if settings.get("shuffle_questions"):
        rng = random.Random(session_id)
        indices = list(range(len(questions)))
        rng.shuffle(indices)
        return questions[indices[question_index]]
    return questions[question_index]


def get_shuffled_options(
    question: Question, settings: dict, session_id: int, question_index: int,
) -> list[QuestionOption]:
    """Get active options, optionally shuffled with deterministic seed."""
    options = sorted(
        [o for o in question.options if not o.is_deleted],
        key=lambda o: o.sort_order,
    )
    if settings.get("shuffle_answers"):
        rng = random.Random(session_id * 10000 + question_index)
        indices = list(range(len(options)))
        rng.shuffle(indices)
        return [options[i] for i in indices]
    return options


async def load_question(
    db: AsyncSession, test_id: int, question_index: int, settings: dict, session_id: int,
) -> Optional[QuizQuestionOut]:
    """Load a single question by index with shuffle and time settings applied."""
    test = await load_test(db, test_id)
    if not test:
        return None

    questions = get_sorted_questions(test)
    q = get_question_at_index(questions, question_index, settings, session_id)
    if not q:
        return None

    time_limit = settings.get("time_per_question_ms", 30000)
    # Teacher-paced mode: no timer
    if settings.get("pacing") == "teacher_paced":
        time_limit = 0

    # Short answer: no option buttons
    q_type = q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type)
    if q_type == "short_answer":
        return QuizQuestionOut(
            index=question_index,
            text=q.question_text,
            question_type="short_answer",
            options=[],
            time_limit_ms=time_limit,
            image_url=None,
        )

    options = get_shuffled_options(q, settings, session_id, question_index)
    return QuizQuestionOut(
        index=question_index,
        text=q.question_text,
        question_type="single_choice",
        options=[o.option_text for o in options],
        time_limit_ms=time_limit,
        image_url=None,
    )


async def check_answer(
    db: AsyncSession, test_id: int, question_index: int, selected_option: int,
    settings: dict, session_id: int,
) -> bool:
    """Check if selected_option is the correct answer (respects shuffle)."""
    test = await load_test(db, test_id)
    if not test:
        return False

    questions = get_sorted_questions(test)
    q = get_question_at_index(questions, question_index, settings, session_id)
    if not q:
        return False

    options = get_shuffled_options(q, settings, session_id, question_index)
    if selected_option < 0 or selected_option >= len(options):
        return False

    return options[selected_option].is_correct


async def get_correct_option_index(
    db: AsyncSession, test_id: int, question_index: int,
    settings: dict, session_id: int,
) -> Optional[int]:
    """Get the index of the correct option (respects shuffle)."""
    test = await load_test(db, test_id)
    if not test:
        return None

    questions = get_sorted_questions(test)
    q = get_question_at_index(questions, question_index, settings, session_id)
    if not q:
        return None

    options = get_shuffled_options(q, settings, session_id, question_index)
    for i, o in enumerate(options):
        if o.is_correct:
            return i
    return None
