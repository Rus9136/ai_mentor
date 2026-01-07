"""
Test Taking Service для workflow прохождения тестов.

Workflow: start → answer → complete → grade → results

Transaction Policy:
- Service добавляет объекты в session (db.add)
- НЕ вызывает commit() — это делает endpoint
- GradingService вызывается после commit и делает свой commit
"""

import logging
from datetime import datetime, timezone
from typing import List, Optional, Dict, Any, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.models.test import Test, Question, TestPurpose, DifficultyLevel
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.repositories.test_attempt_repo import TestAttemptRepository


logger = logging.getLogger(__name__)


class TestTakingService:
    """
    Service для workflow прохождения тестов.

    Responsibilities:
    - Старт теста (создание attempt)
    - Сохранение ответов с inline grading
    - Получение деталей попытки
    - Получение доступных тестов

    Transaction Policy:
    - Добавляет объекты в session (db.add)
    - НЕ вызывает commit() — это делает endpoint
    - При вызове GradingService endpoint делает commit ДО grading
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.test_repo = TestRepository(db)
        self.attempt_repo = TestAttemptRepository(db)
        self.question_repo = QuestionRepository(db)
        self.option_repo = QuestionOptionRepository(db)

    # =========================================================================
    # PUBLIC METHODS
    # =========================================================================

    async def start_test(
        self,
        student_id: int,
        test_id: int,
        school_id: int
    ) -> Dict[str, Any]:
        """
        Начать новую попытку теста.

        Args:
            student_id: ID студента
            test_id: ID теста
            school_id: ID школы

        Returns:
            Dict с attempt данными и вопросами БЕЗ правильных ответов

        Raises:
            ValueError: Test not found, not accessible, or not active
        """
        # 1. Validate test access
        test = await self._validate_test_access(test_id, school_id)

        # 2. Load questions WITHOUT options
        questions = await self.question_repo.get_by_test(test_id, load_options=False)

        # 3. Calculate attempt number
        attempt_count = await self.attempt_repo.count_attempts(
            student_id=student_id,
            test_id=test_id
        )
        attempt_number = attempt_count + 1

        # 4. Create attempt (NOT committed yet!)
        attempt = TestAttempt(
            student_id=student_id,
            test_id=test_id,
            school_id=school_id,
            attempt_number=attempt_number,
            status=AttemptStatus.IN_PROGRESS,
            started_at=datetime.now(timezone.utc)
        )
        attempt = await self.attempt_repo.create(attempt)

        logger.info(
            f"Student {student_id} started test {test_id}, "
            f"attempt #{attempt_number} (id={attempt.id})"
        )

        # 5. Build questions response WITHOUT correct answers
        questions_response = await self._build_questions_for_student(questions)

        return {
            "attempt": attempt,
            "test": test,
            "questions": questions_response
        }

    async def answer_question(
        self,
        attempt_id: int,
        question_id: int,
        selected_option_ids: List[int],
        *,
        student_id: int,
        school_id: int
    ) -> Dict[str, Any]:
        """
        Ответить на вопрос теста с immediate feedback.

        Args:
            attempt_id: ID попытки
            question_id: ID вопроса
            selected_option_ids: Выбранные опции
            student_id: ID студента
            school_id: ID школы

        Returns:
            Dict с feedback: is_correct, correct_option_ids, explanation,
            points_earned, answered_count, total_questions

        Raises:
            ValueError: Attempt not found, wrong status, question not found,
                       or already answered
        """
        # 1. Validate attempt access
        attempt = await self._validate_attempt_access(
            attempt_id, student_id, school_id
        )

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot answer: attempt status is {attempt.status}, "
                "expected IN_PROGRESS"
            )

        # 2. Validate question
        question = await self.question_repo.get_by_id(question_id)
        if not question or question.test_id != attempt.test_id:
            raise ValueError(f"Question {question_id} not found in this test")

        # 3. Check if already answered
        if await self._check_already_answered(attempt_id, question_id):
            raise ValueError(
                f"Question {question_id} already answered in this attempt"
            )

        # 4. Load options and grade
        options = await self.option_repo.get_by_question(question_id)
        correct_option_ids = [opt.id for opt in options if opt.is_correct]

        is_correct, points_earned = self._grade_single_answer(
            question.points, selected_option_ids, correct_option_ids
        )

        # 5. Create answer (NOT committed yet!)
        answer = TestAttemptAnswer(
            attempt_id=attempt_id,
            question_id=question_id,
            selected_option_ids=selected_option_ids,
            is_correct=is_correct,
            points_earned=points_earned,
            answered_at=datetime.now(timezone.utc)
        )
        self.db.add(answer)

        # 6. Count progress
        total_questions = await self._count_test_questions(attempt.test_id)
        answered_count = await self._count_answered_questions(attempt_id) + 1

        logger.info(
            f"Student {student_id} answered Q{question_id} in attempt {attempt_id}: "
            f"correct={is_correct}, points={points_earned}, "
            f"progress={answered_count}/{total_questions}"
        )

        return {
            "question_id": question_id,
            "is_correct": is_correct,
            "correct_option_ids": correct_option_ids,
            "explanation": question.explanation,
            "points_earned": points_earned,
            "answered_count": answered_count,
            "total_questions": total_questions,
            "is_last_question": answered_count >= total_questions
        }

    async def submit_all_answers(
        self,
        attempt_id: int,
        answers: List[Dict[str, Any]],
        *,
        student_id: int,
        school_id: int
    ) -> None:
        """
        Отправить все ответы сразу (bulk submit).

        Args:
            attempt_id: ID попытки
            answers: Список ответов [{question_id, selected_option_ids, answer_text}]
            student_id: ID студента
            school_id: ID школы

        Raises:
            ValueError: Attempt not found, wrong status, or answer count mismatch
        """
        # 1. Validate attempt
        attempt = await self._validate_attempt_access(
            attempt_id, student_id, school_id
        )

        if attempt.status != AttemptStatus.IN_PROGRESS:
            raise ValueError(
                f"Cannot submit: attempt status is {attempt.status}, "
                "expected IN_PROGRESS"
            )

        # 2. Load questions
        questions = await self.question_repo.get_by_test(
            attempt.test_id, load_options=False
        )

        if len(answers) != len(questions):
            raise ValueError(
                f"Answer count mismatch: got {len(answers)} answers, "
                f"expected {len(questions)} questions"
            )

        # 3. Validate and create answers
        question_map = {q.id: q for q in questions}

        for answer_data in answers:
            question_id = answer_data.get("question_id")
            if question_id not in question_map:
                raise ValueError(f"Invalid question_id: {question_id}")

            answer = TestAttemptAnswer(
                attempt_id=attempt_id,
                question_id=question_id,
                selected_option_ids=answer_data.get("selected_option_ids", []),
                answer_text=answer_data.get("answer_text"),
                answered_at=datetime.now(timezone.utc)
            )
            self.db.add(answer)

        logger.info(
            f"Student {student_id} submitted {len(answers)} answers "
            f"for attempt {attempt_id}"
        )

    async def get_attempt_details(
        self,
        attempt_id: int,
        *,
        student_id: int,
        school_id: int
    ) -> Dict[str, Any]:
        """
        Получить детали попытки с вопросами.

        Returns different data based on status:
        - IN_PROGRESS: questions WITHOUT correct answers
        - COMPLETED: questions WITH correct answers and explanations

        Args:
            attempt_id: ID попытки
            student_id: ID студента
            school_id: ID школы

        Returns:
            Dict с attempt, test, questions и answers

        Raises:
            ValueError: Attempt not found or access denied
        """
        # 1. Validate access
        attempt = await self._validate_attempt_access(
            attempt_id, student_id, school_id
        )

        # 2. Load full attempt with answers
        attempt_with_data = await self.attempt_repo.get_with_answers(attempt_id)
        if not attempt_with_data:
            raise ValueError(f"Test attempt {attempt_id} not found")

        # 3. Determine if we show correct answers
        show_correct = attempt_with_data.status != AttemptStatus.IN_PROGRESS

        # 4. Build answers response
        answers_response = []
        for answer in sorted(
            attempt_with_data.answers,
            key=lambda a: a.question.sort_order
        ):
            q = answer.question
            question_data = self._build_question_data(q, show_correct)

            answers_response.append({
                "id": answer.id,
                "attempt_id": answer.attempt_id,
                "question_id": answer.question_id,
                "selected_option_ids": answer.selected_option_ids,
                "answer_text": answer.answer_text,
                "is_correct": answer.is_correct,
                "points_earned": answer.points_earned,
                "answered_at": answer.answered_at,
                "created_at": answer.created_at,
                "updated_at": answer.updated_at,
                "question": question_data
            })

        return {
            "attempt": attempt_with_data,
            "test": attempt_with_data.test,
            "answers": answers_response
        }

    async def get_available_tests(
        self,
        school_id: int,
        student_id: int,
        *,
        page: int = 1,
        page_size: int = 20,
        chapter_id: Optional[int] = None,
        paragraph_id: Optional[int] = None,
        test_purpose: Optional[TestPurpose] = None,
        difficulty: Optional[DifficultyLevel] = None
    ) -> Tuple[List[Dict[str, Any]], int]:
        """
        Получить доступные тесты с метаданными.

        Args:
            school_id: ID школы
            student_id: ID студента
            page: Номер страницы (1-based)
            page_size: Количество элементов на странице
            chapter_id: Фильтр по главе
            paragraph_id: Фильтр по параграфу
            test_purpose: Фильтр по типу теста
            difficulty: Фильтр по сложности

        Returns:
            Tuple of (список тестов с question_count, attempts_count, best_score, общее кол-во)
        """
        # 1. Load tests with pagination (difficulty filter applied at repo level)
        tests, total = await self.test_repo.get_available_for_student_paginated(
            school_id=school_id,
            page=page,
            page_size=page_size,
            chapter_id=chapter_id,
            paragraph_id=paragraph_id,
            test_purpose=test_purpose,
            difficulty=difficulty,
            is_active_only=True
        )

        # 2. Add metadata for each test
        result = []
        for test in tests:
            # Get attempts
            attempts = await self.attempt_repo.get_student_attempts(
                student_id=student_id,
                test_id=test.id,
                school_id=school_id
            )

            attempts_count = len(attempts)
            best_score = None

            completed = [
                a for a in attempts
                if a.status == AttemptStatus.COMPLETED and a.score is not None
            ]
            if completed:
                best_score = max(a.score for a in completed)

            # Count questions
            question_count = await self._count_test_questions(test.id)

            result.append({
                "test": test,
                "question_count": question_count,
                "attempts_count": attempts_count,
                "best_score": best_score
            })

        logger.info(
            f"Student {student_id} retrieved {len(result)} available tests"
        )
        return result, total

    # =========================================================================
    # PRIVATE HELPERS
    # =========================================================================

    async def _validate_test_access(
        self,
        test_id: int,
        school_id: int
    ) -> Test:
        """Validate test exists, is active, and accessible to school."""
        test = await self.test_repo.get_by_id(test_id, load_questions=False)

        if not test:
            raise ValueError(f"Test {test_id} not found")

        if test.school_id is not None and test.school_id != school_id:
            raise ValueError("Test not available for your school")

        if not test.is_active:
            raise ValueError("Test is not available")

        return test

    async def _validate_attempt_access(
        self,
        attempt_id: int,
        student_id: int,
        school_id: int
    ) -> TestAttempt:
        """Validate attempt exists and belongs to student."""
        attempt = await self.attempt_repo.get_by_id(
            attempt_id=attempt_id,
            student_id=student_id,
            school_id=school_id
        )

        if not attempt:
            raise ValueError(
                f"Test attempt {attempt_id} not found or access denied"
            )

        return attempt

    async def _check_already_answered(
        self,
        attempt_id: int,
        question_id: int
    ) -> bool:
        """Check if question was already answered in this attempt."""
        result = await self.db.execute(
            select(TestAttemptAnswer).where(
                TestAttemptAnswer.attempt_id == attempt_id,
                TestAttemptAnswer.question_id == question_id
            )
        )
        return result.scalar_one_or_none() is not None

    def _grade_single_answer(
        self,
        question_points: float,
        selected_option_ids: List[int],
        correct_option_ids: List[int]
    ) -> tuple[bool, float]:
        """
        Grade a single answer.

        Returns:
            Tuple of (is_correct, points_earned)
        """
        is_correct = set(selected_option_ids) == set(correct_option_ids)
        points_earned = question_points if is_correct else 0.0
        return is_correct, points_earned

    async def _count_test_questions(self, test_id: int) -> int:
        """Count questions in a test."""
        result = await self.db.execute(
            select(func.count(Question.id)).where(
                Question.test_id == test_id,
                Question.is_deleted == False
            )
        )
        return result.scalar() or 0

    async def _count_answered_questions(self, attempt_id: int) -> int:
        """Count answered questions in an attempt."""
        result = await self.db.execute(
            select(func.count(TestAttemptAnswer.id)).where(
                TestAttemptAnswer.attempt_id == attempt_id
            )
        )
        return result.scalar() or 0

    async def _build_questions_for_student(
        self,
        questions: List[Question]
    ) -> List[Dict[str, Any]]:
        """Build questions response WITHOUT correct answers (for student)."""
        result = []
        for question in sorted(questions, key=lambda q: q.sort_order):
            options = await self.option_repo.get_by_question(question.id)

            result.append({
                "id": question.id,
                "test_id": question.test_id,
                "sort_order": question.sort_order,
                "question_type": question.question_type,
                "question_text": question.question_text,
                "points": question.points,
                "created_at": question.created_at,
                "updated_at": question.updated_at,
                "options": [
                    {
                        "id": opt.id,
                        "question_id": opt.question_id,
                        "sort_order": opt.sort_order,
                        "option_text": opt.option_text,
                        "created_at": opt.created_at,
                        "updated_at": opt.updated_at,
                    }
                    for opt in options
                ]
            })
        return result

    def _build_question_data(
        self,
        question: Question,
        include_correct: bool
    ) -> Dict[str, Any]:
        """Build question data with or without correct answers."""
        data = {
            "id": question.id,
            "test_id": question.test_id,
            "sort_order": question.sort_order,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "points": question.points,
            "created_at": question.created_at,
            "updated_at": question.updated_at,
            "options": []
        }

        if include_correct:
            data["explanation"] = question.explanation
            data["deleted_at"] = question.deleted_at
            data["is_deleted"] = question.is_deleted

        return data
