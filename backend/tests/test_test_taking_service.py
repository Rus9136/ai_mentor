"""
Unit tests for TestTakingService.

Tests cover:
- start_test: test start, validation errors
- answer_question: correct/incorrect answers, already answered
- submit_all_answers: bulk submit, validation
- get_attempt_details: in_progress vs completed
- get_available_tests: filtering, metadata
"""

import pytest
import pytest_asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.test_taking_service import TestTakingService
from app.models.test import Test, Question, QuestionOption, TestPurpose, DifficultyLevel
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.school import School
from app.models.student import Student
from app.models.user import User


class TestTestTakingServiceStartTest:
    """Tests for start_test method."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> TestTakingService:
        """Create service instance."""
        return TestTakingService(db_session)

    async def test_start_test_success(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ):
        """Test successful test start."""
        user, student = student_user

        result = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()

        assert "attempt" in result
        assert "test" in result
        assert "questions" in result

        attempt = result["attempt"]
        assert attempt.student_id == student.id
        assert attempt.test_id == test_with_questions.id
        assert attempt.status == AttemptStatus.IN_PROGRESS
        assert attempt.attempt_number == 1

        # Questions should not contain is_correct
        questions = result["questions"]
        assert len(questions) > 0
        for q in questions:
            for opt in q.get("options", []):
                assert "is_correct" not in opt

    async def test_start_test_not_found(
        self,
        service: TestTakingService,
        student_user: tuple[User, Student]
    ):
        """Test start with non-existent test."""
        user, student = student_user

        with pytest.raises(ValueError) as exc_info:
            await service.start_test(
                student_id=student.id,
                test_id=99999,
                school_id=student.school_id
            )

        assert "not found" in str(exc_info.value)

    async def test_start_test_wrong_school(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        school2: School,
        chapter1,
        paragraph1
    ):
        """Test start with test from different school."""
        user, student = student_user

        # Create test in school2
        test = Test(
            school_id=school2.id,
            chapter_id=chapter1.id,
            paragraph_id=paragraph1.id,
            title="School 2 Test",
            test_purpose=TestPurpose.FORMATIVE,
            difficulty=DifficultyLevel.EASY,
            passing_score=0.7,
            is_active=True,
        )
        db_session.add(test)
        await db_session.commit()

        with pytest.raises(ValueError) as exc_info:
            await service.start_test(
                student_id=student.id,
                test_id=test.id,
                school_id=student.school_id  # school1
            )

        assert "not available" in str(exc_info.value)

    async def test_start_test_inactive(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        school1: School,
        chapter1,
        paragraph1
    ):
        """Test start with inactive test."""
        user, student = student_user

        # Create inactive test
        test = Test(
            school_id=school1.id,
            chapter_id=chapter1.id,
            paragraph_id=paragraph1.id,
            title="Inactive Test",
            test_purpose=TestPurpose.FORMATIVE,
            difficulty=DifficultyLevel.EASY,
            passing_score=0.7,
            is_active=False,
        )
        db_session.add(test)
        await db_session.commit()

        with pytest.raises(ValueError) as exc_info:
            await service.start_test(
                student_id=student.id,
                test_id=test.id,
                school_id=student.school_id
            )

        assert "not available" in str(exc_info.value)

    async def test_start_test_increments_attempt_number(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ):
        """Test that attempt number increments correctly."""
        user, student = student_user

        # Start first attempt
        result1 = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()
        assert result1["attempt"].attempt_number == 1

        # Start second attempt
        result2 = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()
        assert result2["attempt"].attempt_number == 2


class TestTestTakingServiceAnswerQuestion:
    """Tests for answer_question method."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> TestTakingService:
        """Create service instance."""
        return TestTakingService(db_session)

    @pytest_asyncio.fixture
    async def active_attempt(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ) -> TestAttempt:
        """Create an active test attempt."""
        user, student = student_user
        result = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()
        return result["attempt"]

    async def test_answer_question_correct(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        active_attempt: TestAttempt
    ):
        """Test answering correctly."""
        user, student = student_user

        # Get first question (SINGLE_CHOICE)
        q_result = await db_session.execute(
            select(Question).where(Question.test_id == test_with_questions.id)
        )
        questions = q_result.scalars().all()
        question = questions[0]

        # Get correct option
        opt_result = await db_session.execute(
            select(QuestionOption).where(
                QuestionOption.question_id == question.id,
                QuestionOption.is_correct == True
            )
        )
        correct_option = opt_result.scalar_one()

        result = await service.answer_question(
            attempt_id=active_attempt.id,
            question_id=question.id,
            selected_option_ids=[correct_option.id],
            student_id=student.id,
            school_id=student.school_id
        )
        await db_session.commit()

        assert result["is_correct"] is True
        assert result["points_earned"] == question.points
        assert correct_option.id in result["correct_option_ids"]
        assert result["explanation"] == question.explanation

    async def test_answer_question_incorrect(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        active_attempt: TestAttempt
    ):
        """Test answering incorrectly."""
        user, student = student_user

        # Get first question
        q_result = await db_session.execute(
            select(Question).where(Question.test_id == test_with_questions.id)
        )
        questions = q_result.scalars().all()
        question = questions[0]

        # Get incorrect option
        opt_result = await db_session.execute(
            select(QuestionOption).where(
                QuestionOption.question_id == question.id,
                QuestionOption.is_correct == False
            )
        )
        wrong_option = opt_result.scalars().first()

        result = await service.answer_question(
            attempt_id=active_attempt.id,
            question_id=question.id,
            selected_option_ids=[wrong_option.id],
            student_id=student.id,
            school_id=student.school_id
        )
        await db_session.commit()

        assert result["is_correct"] is False
        assert result["points_earned"] == 0.0

    async def test_answer_question_already_answered(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        active_attempt: TestAttempt
    ):
        """Test answering same question twice."""
        user, student = student_user

        # Get first question
        q_result = await db_session.execute(
            select(Question).where(Question.test_id == test_with_questions.id)
        )
        questions = q_result.scalars().all()
        question = questions[0]

        # Get any option
        opt_result = await db_session.execute(
            select(QuestionOption).where(QuestionOption.question_id == question.id)
        )
        option = opt_result.scalars().first()

        # Answer first time
        await service.answer_question(
            attempt_id=active_attempt.id,
            question_id=question.id,
            selected_option_ids=[option.id],
            student_id=student.id,
            school_id=student.school_id
        )
        await db_session.commit()

        # Try to answer again
        with pytest.raises(ValueError) as exc_info:
            await service.answer_question(
                attempt_id=active_attempt.id,
                question_id=question.id,
                selected_option_ids=[option.id],
                student_id=student.id,
                school_id=student.school_id
            )

        assert "already answered" in str(exc_info.value)

    async def test_answer_question_not_in_test(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        active_attempt: TestAttempt
    ):
        """Test answering question not in this test."""
        user, student = student_user

        with pytest.raises(ValueError) as exc_info:
            await service.answer_question(
                attempt_id=active_attempt.id,
                question_id=99999,
                selected_option_ids=[1],
                student_id=student.id,
                school_id=student.school_id
            )

        assert "not found" in str(exc_info.value)

    async def test_answer_question_attempt_not_found(
        self,
        service: TestTakingService,
        student_user: tuple[User, Student]
    ):
        """Test answering with non-existent attempt."""
        user, student = student_user

        with pytest.raises(ValueError) as exc_info:
            await service.answer_question(
                attempt_id=99999,
                question_id=1,
                selected_option_ids=[1],
                student_id=student.id,
                school_id=student.school_id
            )

        assert "not found" in str(exc_info.value)


class TestTestTakingServiceSubmitAllAnswers:
    """Tests for submit_all_answers method."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> TestTakingService:
        """Create service instance."""
        return TestTakingService(db_session)

    @pytest_asyncio.fixture
    async def active_attempt(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ) -> TestAttempt:
        """Create an active test attempt."""
        user, student = student_user
        result = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()
        return result["attempt"]

    async def test_submit_all_answers_success(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        active_attempt: TestAttempt
    ):
        """Test successful bulk submit."""
        user, student = student_user

        # Get all questions
        q_result = await db_session.execute(
            select(Question).where(Question.test_id == test_with_questions.id)
        )
        questions = q_result.scalars().all()

        # Build answers
        answers = []
        for q in questions:
            opt_result = await db_session.execute(
                select(QuestionOption).where(QuestionOption.question_id == q.id)
            )
            options = opt_result.scalars().all()
            answers.append({
                "question_id": q.id,
                "selected_option_ids": [options[0].id] if options else [],
                "answer_text": None
            })

        await service.submit_all_answers(
            attempt_id=active_attempt.id,
            answers=answers,
            student_id=student.id,
            school_id=student.school_id
        )
        await db_session.commit()

        # Check answers were created
        ans_result = await db_session.execute(
            select(TestAttemptAnswer).where(
                TestAttemptAnswer.attempt_id == active_attempt.id
            )
        )
        saved_answers = ans_result.scalars().all()
        assert len(saved_answers) == len(questions)

    async def test_submit_all_answers_count_mismatch(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        active_attempt: TestAttempt
    ):
        """Test submit with wrong number of answers."""
        user, student = student_user

        # Submit only one answer
        answers = [{"question_id": 1, "selected_option_ids": [1]}]

        with pytest.raises(ValueError) as exc_info:
            await service.submit_all_answers(
                attempt_id=active_attempt.id,
                answers=answers,
                student_id=student.id,
                school_id=student.school_id
            )

        assert "mismatch" in str(exc_info.value)

    async def test_submit_all_answers_attempt_completed(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        active_attempt: TestAttempt
    ):
        """Test submit on already completed attempt."""
        user, student = student_user

        # Mark attempt as completed
        active_attempt.status = AttemptStatus.COMPLETED
        await db_session.commit()

        with pytest.raises(ValueError) as exc_info:
            await service.submit_all_answers(
                attempt_id=active_attempt.id,
                answers=[],
                student_id=student.id,
                school_id=student.school_id
            )

        assert "IN_PROGRESS" in str(exc_info.value)


class TestTestTakingServiceGetAttemptDetails:
    """Tests for get_attempt_details method."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> TestTakingService:
        """Create service instance."""
        return TestTakingService(db_session)

    async def test_get_attempt_details_in_progress(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ):
        """Test getting details for in-progress attempt."""
        user, student = student_user

        # Start attempt
        start_result = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()
        attempt = start_result["attempt"]

        result = await service.get_attempt_details(
            attempt_id=attempt.id,
            student_id=student.id,
            school_id=student.school_id
        )

        assert result["attempt"].status == AttemptStatus.IN_PROGRESS
        assert "test" in result
        assert "answers" in result

    async def test_get_attempt_details_not_found(
        self,
        service: TestTakingService,
        student_user: tuple[User, Student]
    ):
        """Test getting non-existent attempt."""
        user, student = student_user

        with pytest.raises(ValueError) as exc_info:
            await service.get_attempt_details(
                attempt_id=99999,
                student_id=student.id,
                school_id=student.school_id
            )

        assert "not found" in str(exc_info.value)


class TestTestTakingServiceGetAvailableTests:
    """Tests for get_available_tests method."""

    @pytest_asyncio.fixture
    async def service(self, db_session: AsyncSession) -> TestTakingService:
        """Create service instance."""
        return TestTakingService(db_session)

    async def test_get_available_tests(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ):
        """Test getting available tests."""
        user, student = student_user

        result = await service.get_available_tests(
            school_id=student.school_id,
            student_id=student.id
        )

        assert len(result) >= 1
        test_item = result[0]
        assert "test" in test_item
        assert "question_count" in test_item
        assert "attempts_count" in test_item
        assert "best_score" in test_item

    async def test_get_available_tests_with_attempts(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test
    ):
        """Test that attempts_count and best_score are calculated."""
        user, student = student_user

        # Start and complete an attempt
        start_result = await service.start_test(
            student_id=student.id,
            test_id=test_with_questions.id,
            school_id=student.school_id
        )
        await db_session.commit()

        attempt = start_result["attempt"]
        attempt.status = AttemptStatus.COMPLETED
        attempt.score = 0.85
        await db_session.commit()

        result = await service.get_available_tests(
            school_id=student.school_id,
            student_id=student.id
        )

        test_item = next(
            t for t in result if t["test"].id == test_with_questions.id
        )
        assert test_item["attempts_count"] == 1
        assert test_item["best_score"] == 0.85

    async def test_get_available_tests_filters(
        self,
        service: TestTakingService,
        db_session: AsyncSession,
        student_user: tuple[User, Student],
        test_with_questions: Test,
        chapter1
    ):
        """Test filtering by chapter_id."""
        user, student = student_user

        result = await service.get_available_tests(
            school_id=student.school_id,
            student_id=student.id,
            chapter_id=chapter1.id
        )

        # Should only return tests for this chapter
        for item in result:
            assert item["test"].chapter_id == chapter1.id
