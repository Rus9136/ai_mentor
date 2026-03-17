"""
Quiz question loader: test loading, question shuffling, answer checking.
Extracted from quiz_service.py for reuse across quiz modules.

Supports three question sources:
1. test_id — all questions from a single test (legacy)
2. question_ids — cherry-picked questions from multiple tests (stored in settings)
3. custom_questions — teacher-created inline questions (stored in settings)
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


async def _load_questions_by_ids(db: AsyncSession, question_ids: list[int]) -> list[Question]:
    """Load specific questions by IDs, preserving order from question_ids."""
    result = await db.execute(
        select(Question)
        .options(selectinload(Question.options))
        .where(Question.id.in_(question_ids), Question.is_deleted == False)
    )
    questions = result.scalars().all()
    id_to_q = {q.id: q for q in questions}
    return [id_to_q[qid] for qid in question_ids if qid in id_to_q]


def _get_total_question_count(settings: dict, test_question_count: int = 0) -> int:
    """Calculate total questions from bank + custom."""
    bank_count = len(settings.get("question_ids", [])) if settings.get("question_ids") else test_question_count
    custom_count = len(settings.get("custom_questions", []))
    return bank_count + custom_count


async def _resolve_questions(
    db: AsyncSession, test_id: Optional[int], settings: dict,
) -> list[Question]:
    """Resolve the list of DB Question objects based on settings."""
    question_ids = settings.get("question_ids")
    if question_ids:
        return await _load_questions_by_ids(db, question_ids)
    if test_id:
        test = await load_test(db, test_id)
        if test:
            return get_sorted_questions(test)
    return []


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


def _build_question_out(
    question_index: int, text: str, question_type: str,
    option_texts: list[str], time_limit: int,
) -> QuizQuestionOut:
    return QuizQuestionOut(
        index=question_index,
        text=text,
        question_type=question_type,
        options=option_texts,
        time_limit_ms=time_limit,
        image_url=None,
    )


def _get_time_limit(settings: dict) -> int:
    time_limit = settings.get("time_per_question_ms", 30000)
    if settings.get("pacing") == "teacher_paced":
        time_limit = 0
    return time_limit


def _try_custom_question(
    question_index: int, settings: dict, bank_count: int, session_id: int,
) -> Optional[QuizQuestionOut]:
    """If question_index falls into custom_questions range, return it."""
    custom_questions = settings.get("custom_questions", [])
    if not custom_questions:
        return None
    custom_index = question_index - bank_count
    if custom_index < 0 or custom_index >= len(custom_questions):
        return None
    cq = custom_questions[custom_index]
    time_limit = _get_time_limit(settings)
    options = list(cq["options"])
    if settings.get("shuffle_answers"):
        rng = random.Random(session_id * 10000 + question_index)
        # Shuffle while tracking correct answer
        correct_idx = cq["correct_option"]
        indexed = list(enumerate(options))
        rng.shuffle(indexed)
        options = [o for _, o in indexed]
        # Update correct_option in shuffled order (for answer checking)
        # Not modifying settings — checked separately
    return _build_question_out(question_index, cq["question_text"], "single_choice", options, time_limit)


async def load_question(
    db: AsyncSession, test_id: int, question_index: int, settings: dict, session_id: int,
) -> Optional[QuizQuestionOut]:
    """Load a single question by index with shuffle and time settings applied.

    Supports: test_id, question_ids, and custom_questions (bank first, then custom).
    """
    bank_questions = await _resolve_questions(db, test_id, settings)
    bank_count = len(bank_questions)

    # Check if this index falls into custom_questions
    if question_index >= bank_count:
        return _try_custom_question(question_index, settings, bank_count, session_id)

    # Bank question (from test or question_ids)
    q = get_question_at_index(bank_questions, question_index, settings, session_id)
    if not q:
        return _try_custom_question(question_index, settings, bank_count, session_id)

    time_limit = _get_time_limit(settings)

    q_type = q.question_type.value if hasattr(q.question_type, 'value') else str(q.question_type)
    if q_type == "short_answer":
        return _build_question_out(question_index, q.question_text, "short_answer", [], time_limit)

    options = get_shuffled_options(q, settings, session_id, question_index)
    return _build_question_out(
        question_index, q.question_text, "single_choice",
        [o.option_text for o in options], time_limit,
    )


async def check_answer(
    db: AsyncSession, test_id: int, question_index: int, selected_option: int,
    settings: dict, session_id: int,
) -> bool:
    """Check if selected_option is the correct answer (respects shuffle)."""
    bank_questions = await _resolve_questions(db, test_id, settings)
    bank_count = len(bank_questions)

    # Custom question
    if question_index >= bank_count:
        custom_questions = settings.get("custom_questions", [])
        custom_index = question_index - bank_count
        if custom_index < 0 or custom_index >= len(custom_questions):
            return False
        cq = custom_questions[custom_index]
        correct = cq["correct_option"]
        if settings.get("shuffle_answers"):
            rng = random.Random(session_id * 10000 + question_index)
            indices = list(range(len(cq["options"])))
            rng.shuffle(indices)
            # indices[selected_option] maps to original index
            return indices[selected_option] == correct
        return selected_option == correct

    # Bank question
    q = get_question_at_index(bank_questions, question_index, settings, session_id)
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
    bank_questions = await _resolve_questions(db, test_id, settings)
    bank_count = len(bank_questions)

    # Custom question
    if question_index >= bank_count:
        custom_questions = settings.get("custom_questions", [])
        custom_index = question_index - bank_count
        if custom_index < 0 or custom_index >= len(custom_questions):
            return None
        cq = custom_questions[custom_index]
        correct = cq["correct_option"]
        if settings.get("shuffle_answers"):
            rng = random.Random(session_id * 10000 + question_index)
            indices = list(range(len(cq["options"])))
            rng.shuffle(indices)
            for i, orig in enumerate(indices):
                if orig == correct:
                    return i
            return None
        return correct

    # Bank question
    q = get_question_at_index(bank_questions, question_index, settings, session_id)
    if not q:
        return None

    options = get_shuffled_options(q, settings, session_id, question_index)
    for i, o in enumerate(options):
        if o.is_correct:
            return i
    return None
