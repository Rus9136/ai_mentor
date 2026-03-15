"""
Short Answer checking service for Quiz Battle (Phase 2.3).
Three-tier checking: exact match → fuzzy match → LLM fallback.
"""
import asyncio
import logging
from difflib import SequenceMatcher
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.test import Test, Question, QuestionOption, QuestionType

logger = logging.getLogger(__name__)

FUZZY_THRESHOLD = 0.85
LLM_TIMEOUT_SECONDS = 5


class QuizShortAnswerService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def check_answer(
        self,
        test_id: int,
        question_index: int,
        student_answer: str,
        settings: dict,
        session_id: int,
    ) -> tuple[bool, str]:
        """Check a short answer. Returns (is_correct, method)."""
        # Load the question and its correct option(s)
        correct_texts = await self._get_correct_texts(test_id, question_index, settings, session_id)
        if not correct_texts:
            return False, "no_correct"

        normalized = student_answer.strip().lower()
        if not normalized:
            return False, "empty"

        # 1. Exact match
        for ct in correct_texts:
            if normalized == ct.strip().lower():
                return True, "exact"

        # 2. Fuzzy match
        best_ratio = 0.0
        for ct in correct_texts:
            ratio = SequenceMatcher(None, normalized, ct.strip().lower()).ratio()
            best_ratio = max(best_ratio, ratio)
        if best_ratio >= FUZZY_THRESHOLD:
            return True, "fuzzy"

        # 3. LLM fallback
        question_text = await self._get_question_text(test_id, question_index, settings, session_id)
        if question_text:
            try:
                result = await asyncio.wait_for(
                    self._llm_check(question_text, correct_texts[0], student_answer),
                    timeout=LLM_TIMEOUT_SECONDS,
                )
                return result, "llm"
            except (asyncio.TimeoutError, Exception) as e:
                logger.warning(f"LLM check failed for short answer: {e}")

        return False, "no_match"

    async def _get_correct_texts(
        self, test_id: int, question_index: int, settings: dict, session_id: int,
    ) -> list[str]:
        """Get correct option texts for the question at the given index."""
        from app.services.quiz_question_loader import (
            load_test, get_sorted_questions, get_question_at_index,
        )
        test = await load_test(self.db, test_id)
        if not test:
            return []
        questions = get_sorted_questions(test)
        q = get_question_at_index(questions, question_index, settings, session_id)
        if not q:
            return []
        return [o.option_text for o in q.options if o.is_correct and not o.is_deleted]

    async def _get_question_text(
        self, test_id: int, question_index: int, settings: dict, session_id: int,
    ) -> Optional[str]:
        from app.services.quiz_question_loader import (
            load_test, get_sorted_questions, get_question_at_index,
        )
        test = await load_test(self.db, test_id)
        if not test:
            return None
        questions = get_sorted_questions(test)
        q = get_question_at_index(questions, question_index, settings, session_id)
        return q.question_text if q else None

    async def _llm_check(self, question_text: str, correct_answer: str, student_answer: str) -> bool:
        """Use LLM to check if student's answer is semantically correct."""
        from app.services.llm_service import LLMService
        llm = LLMService()

        prompt = (
            f"You are grading a student's short answer.\n\n"
            f"Question: {question_text}\n"
            f"Expected answer: {correct_answer}\n"
            f"Student's answer: {student_answer}\n\n"
            f"Is the student's answer semantically correct? Consider spelling variations, "
            f"synonyms, and partial answers. Respond with exactly CORRECT or INCORRECT."
        )

        try:
            response = await llm.generate(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                max_tokens=10,
            )
            content = response.get("content", "") if isinstance(response, dict) else str(response)
            return "CORRECT" in content.upper() and "INCORRECT" not in content.upper()
        except Exception as e:
            logger.error(f"LLM short answer check failed: {e}")
            return False
