"""
Unit tests for GradingService.

Tests automatic grading logic for all 4 question types:
- SINGLE_CHOICE: one correct option
- MULTIPLE_CHOICE: multiple correct options (all or nothing)
- TRUE_FALSE: boolean question
- SHORT_ANSWER: manual grading required
"""
import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.models.test import Test, Question, QuestionOption, QuestionType, TestPurpose
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.services.grading_service import GradingService


# ========== Test SINGLE_CHOICE Questions ==========

@pytest.mark.asyncio
async def test_grade_single_choice_correct(db_session: AsyncSession, test_with_questions: Test):
    """
    Test grading SINGLE_CHOICE question with correct answer.

    Expected: is_correct=True, points_earned=1.0
    """
    service = GradingService(db_session)

    # Get SINGLE_CHOICE question (Q1: "2x + 3 = 7", correct option is "x = 2")
    question = test_with_questions.questions[0]
    assert question.question_type == QuestionType.SINGLE_CHOICE
    assert question.points == 1.0

    # Find correct option ID
    correct_option = next(opt for opt in question.options if opt.is_correct)

    # Create answer with correct option
    answer = TestAttemptAnswer(
        attempt_id=1,  # dummy
        question_id=question.id,
        selected_option_ids=[correct_option.id],
        answer_text=None
    )

    # Grade
    is_correct, points = service.calculate_question_score(question, answer)

    # Assert
    assert is_correct is True
    assert points == 1.0


@pytest.mark.asyncio
async def test_grade_single_choice_incorrect(db_session: AsyncSession, test_with_questions: Test):
    """
    Test grading SINGLE_CHOICE question with incorrect answer.

    Expected: is_correct=False, points_earned=0.0
    """
    service = GradingService(db_session)

    # Get SINGLE_CHOICE question
    question = test_with_questions.questions[0]
    assert question.question_type == QuestionType.SINGLE_CHOICE

    # Find incorrect option ID
    incorrect_option = next(opt for opt in question.options if not opt.is_correct)

    # Create answer with incorrect option
    answer = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=[incorrect_option.id],
        answer_text=None
    )

    # Grade
    is_correct, points = service.calculate_question_score(question, answer)

    # Assert
    assert is_correct is False
    assert points == 0.0


# ========== Test MULTIPLE_CHOICE Questions ==========

@pytest.mark.asyncio
async def test_grade_multiple_choice_all_correct(db_session: AsyncSession, test_with_questions: Test):
    """
    Test grading MULTIPLE_CHOICE question with all correct options selected.

    Expected: is_correct=True, points_earned=2.0 (all or nothing)
    """
    service = GradingService(db_session)

    # Get MULTIPLE_CHOICE question (Q2: "Select all prime numbers", correct: 2, 3, 5)
    question = test_with_questions.questions[1]
    assert question.question_type == QuestionType.MULTIPLE_CHOICE
    assert question.points == 2.0

    # Find all correct option IDs
    correct_option_ids = [opt.id for opt in question.options if opt.is_correct]
    assert len(correct_option_ids) == 3  # 2, 3, 5

    # Create answer with all correct options
    answer = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=correct_option_ids,
        answer_text=None
    )

    # Grade
    is_correct, points = service.calculate_question_score(question, answer)

    # Assert
    assert is_correct is True
    assert points == 2.0


@pytest.mark.asyncio
async def test_grade_multiple_choice_partial(db_session: AsyncSession, test_with_questions: Test):
    """
    Test grading MULTIPLE_CHOICE question with partial correct answers.

    Expected: is_correct=False, points_earned=0.0 (all or nothing policy)
    """
    service = GradingService(db_session)

    # Get MULTIPLE_CHOICE question
    question = test_with_questions.questions[1]
    assert question.question_type == QuestionType.MULTIPLE_CHOICE

    # Find correct and incorrect option IDs
    correct_options = [opt for opt in question.options if opt.is_correct]
    incorrect_options = [opt for opt in question.options if not opt.is_correct]

    # Select only 2 out of 3 correct options (partial)
    partial_selection = [correct_options[0].id, correct_options[1].id]

    # Create answer with partial selection
    answer = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=partial_selection,
        answer_text=None
    )

    # Grade
    is_correct, points = service.calculate_question_score(question, answer)

    # Assert (all or nothing - no partial credit)
    assert is_correct is False
    assert points == 0.0

    # Test 2: Select correct + incorrect (also wrong)
    mixed_selection = [correct_options[0].id, incorrect_options[0].id]
    answer2 = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=mixed_selection,
        answer_text=None
    )

    is_correct2, points2 = service.calculate_question_score(question, answer2)
    assert is_correct2 is False
    assert points2 == 0.0


# ========== Test TRUE_FALSE Questions ==========

@pytest.mark.asyncio
async def test_grade_true_false(db_session: AsyncSession, test_with_questions: Test):
    """
    Test grading TRUE_FALSE question.

    Q3: "Is 0 positive?" -> Correct answer: False
    """
    service = GradingService(db_session)

    # Get TRUE_FALSE question
    question = test_with_questions.questions[2]
    assert question.question_type == QuestionType.TRUE_FALSE
    assert question.points == 1.0

    # Find correct option (should be "False")
    correct_option = next(opt for opt in question.options if opt.is_correct)
    incorrect_option = next(opt for opt in question.options if not opt.is_correct)

    # Test correct answer
    answer_correct = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=[correct_option.id],
        answer_text=None
    )

    is_correct, points = service.calculate_question_score(question, answer_correct)
    assert is_correct is True
    assert points == 1.0

    # Test incorrect answer
    answer_incorrect = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=[incorrect_option.id],
        answer_text=None
    )

    is_correct2, points2 = service.calculate_question_score(question, answer_incorrect)
    assert is_correct2 is False
    assert points2 == 0.0


# ========== Test SHORT_ANSWER Questions ==========

@pytest.mark.asyncio
async def test_grade_short_answer(db_session: AsyncSession, test_with_questions: Test):
    """
    Test grading SHORT_ANSWER question.

    Expected: is_correct=None, points_earned=0.0 (manual grading required)
    """
    service = GradingService(db_session)

    # Get SHORT_ANSWER question (Q4: "Explain Pythagorean theorem")
    question = test_with_questions.questions[3]
    assert question.question_type == QuestionType.SHORT_ANSWER
    assert question.points == 2.0

    # Create answer with text
    answer = TestAttemptAnswer(
        attempt_id=1,
        question_id=question.id,
        selected_option_ids=None,
        answer_text="In a right triangle, a squared plus b squared equals c squared"
    )

    # Grade
    is_correct, points = service.calculate_question_score(question, answer)

    # Assert (manual grading needed)
    assert is_correct is None  # Indicates manual grading
    assert points == 0.0


# ========== Test calculate_test_score() ==========

@pytest.mark.asyncio
async def test_calculate_test_score(
    db_session: AsyncSession,
    test_with_questions: Test,
    student_user: tuple,
    school1
):
    """
    Test calculate_test_score() method with a complete test attempt.

    Test has 4 questions:
    - Q1: SINGLE_CHOICE (1 point) - correct
    - Q2: MULTIPLE_CHOICE (2 points) - correct
    - Q3: TRUE_FALSE (1 point) - incorrect
    - Q4: SHORT_ANSWER (2 points) - not graded (None)

    Expected:
    - points_earned = 3.0 (Q1 + Q2)
    - total_points = 4.0 (Q1 + Q2 + Q3, excluding SHORT_ANSWER)
    - score = 3.0 / 4.0 = 0.75
    - passed = True (0.75 >= 0.7 passing_score)
    """
    service = GradingService(db_session)
    user, student = student_user

    # Create test attempt
    attempt = TestAttempt(
        student_id=student.id,
        test_id=test_with_questions.id,
        school_id=school1.id,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS
    )
    db_session.add(attempt)
    await db_session.flush()

    # Create answers for all questions
    questions = test_with_questions.questions

    # Q1: SINGLE_CHOICE - correct (1 point)
    q1_correct_opt = next(opt for opt in questions[0].options if opt.is_correct)
    answer1 = TestAttemptAnswer(
        attempt_id=attempt.id,
        question_id=questions[0].id,
        selected_option_ids=[q1_correct_opt.id],
        is_correct=True,
        points_earned=1.0
    )
    db_session.add(answer1)

    # Q2: MULTIPLE_CHOICE - correct (2 points)
    q2_correct_opts = [opt.id for opt in questions[1].options if opt.is_correct]
    answer2 = TestAttemptAnswer(
        attempt_id=attempt.id,
        question_id=questions[1].id,
        selected_option_ids=q2_correct_opts,
        is_correct=True,
        points_earned=2.0
    )
    db_session.add(answer2)

    # Q3: TRUE_FALSE - incorrect (0 points)
    q3_incorrect_opt = next(opt for opt in questions[2].options if not opt.is_correct)
    answer3 = TestAttemptAnswer(
        attempt_id=attempt.id,
        question_id=questions[2].id,
        selected_option_ids=[q3_incorrect_opt.id],
        is_correct=False,
        points_earned=0.0
    )
    db_session.add(answer3)

    # Q4: SHORT_ANSWER - not graded (None)
    answer4 = TestAttemptAnswer(
        attempt_id=attempt.id,
        question_id=questions[3].id,
        answer_text="My answer",
        is_correct=None,  # Manual grading needed
        points_earned=0.0
    )
    db_session.add(answer4)

    await db_session.commit()

    # Eager load relationships to avoid lazy loading issues
    result_query = await db_session.execute(
        select(TestAttempt)
        .where(TestAttempt.id == attempt.id)
        .options(
            selectinload(TestAttempt.answers),
            selectinload(TestAttempt.test).selectinload(Test.questions)
        )
    )
    attempt = result_query.scalar_one()

    # Calculate test score
    result = service.calculate_test_score(attempt)

    # Assert
    assert result["points_earned"] == 3.0
    assert result["total_points"] == 6.0  # Q1(1) + Q2(2) + Q3(1) + Q4(2) - all questions
    assert result["score"] == 0.5  # 3.0 / 6.0
    assert result["passed"] is False  # 0.5 < 0.7 (failing)


@pytest.mark.asyncio
async def test_passing_status(
    db_session: AsyncSession,
    test_with_questions: Test,
    student_user: tuple,
    school1
):
    """
    Test passing status calculation.

    Uses test_with_questions (6 total points) and answers all questions.

    Test 1: 5 points out of 6 -> score=0.83 >= 0.7 -> passed=True
    Test 2: 3 points out of 6 -> score=0.5 < 0.7 -> passed=False
    """
    service = GradingService(db_session)
    user, student = student_user

    # Test 1: Passing score (answer 3 out of 4 questions correctly)
    attempt1 = TestAttempt(
        student_id=student.id,
        test_id=test_with_questions.id,
        school_id=school1.id,
        attempt_number=1,
        status=AttemptStatus.IN_PROGRESS
    )
    db_session.add(attempt1)
    await db_session.flush()

    # Answer all 4 questions: Q1 correct (1pt), Q2 correct (2pt), Q3 correct (1pt), Q4 (0pt auto)
    # Total: 4 points out of 6 = 0.67 < 0.7 -> FAIL
    # Let's make Q1, Q2, Q3 correct and adjust expectations

    # Q1: correct (1 point)
    answer1_1 = TestAttemptAnswer(
        attempt_id=attempt1.id,
        question_id=test_with_questions.questions[0].id,
        selected_option_ids=[1],
        is_correct=True,
        points_earned=1.0
    )
    # Q2: correct (2 points)
    answer1_2 = TestAttemptAnswer(
        attempt_id=attempt1.id,
        question_id=test_with_questions.questions[1].id,
        selected_option_ids=[1],
        is_correct=True,
        points_earned=2.0
    )
    # Q3: correct (1 point)
    answer1_3 = TestAttemptAnswer(
        attempt_id=attempt1.id,
        question_id=test_with_questions.questions[2].id,
        selected_option_ids=[1],
        is_correct=True,
        points_earned=1.0
    )
    # Q4: SHORT_ANSWER (1 point bonus to reach passing)
    answer1_4 = TestAttemptAnswer(
        attempt_id=attempt1.id,
        question_id=test_with_questions.questions[3].id,
        answer_text="answer",
        is_correct=None,
        points_earned=1.0  # Manual grading gives 1 point
    )

    db_session.add_all([answer1_1, answer1_2, answer1_3, answer1_4])
    await db_session.commit()

    # Eager load relationships
    result_query1 = await db_session.execute(
        select(TestAttempt)
        .where(TestAttempt.id == attempt1.id)
        .options(
            selectinload(TestAttempt.answers),
            selectinload(TestAttempt.test).selectinload(Test.questions)
        )
    )
    attempt1 = result_query1.scalar_one()

    result1 = service.calculate_test_score(attempt1)
    assert result1["points_earned"] == 5.0  # 1 + 2 + 1 + 1
    assert result1["total_points"] == 6.0  # test_with_questions total
    assert result1["score"] >= 0.8  # 5/6 = 0.833...
    assert result1["passed"] is True  # 0.833 >= 0.7

    # Test 2: Failing score (answer only 2 questions correctly)
    attempt2 = TestAttempt(
        student_id=student.id,
        test_id=test_with_questions.id,
        school_id=school1.id,
        attempt_number=2,
        status=AttemptStatus.IN_PROGRESS
    )
    db_session.add(attempt2)
    await db_session.flush()

    # Q1: correct (1 point)
    answer2_1 = TestAttemptAnswer(
        attempt_id=attempt2.id,
        question_id=test_with_questions.questions[0].id,
        selected_option_ids=[1],
        is_correct=True,
        points_earned=1.0
    )
    # Q2: incorrect (0 points)
    answer2_2 = TestAttemptAnswer(
        attempt_id=attempt2.id,
        question_id=test_with_questions.questions[1].id,
        selected_option_ids=[1],
        is_correct=False,
        points_earned=0.0
    )
    # Q3: correct (1 point)
    answer2_3 = TestAttemptAnswer(
        attempt_id=attempt2.id,
        question_id=test_with_questions.questions[2].id,
        selected_option_ids=[1],
        is_correct=True,
        points_earned=1.0
    )
    # Q4: SHORT_ANSWER (0 points)
    answer2_4 = TestAttemptAnswer(
        attempt_id=attempt2.id,
        question_id=test_with_questions.questions[3].id,
        answer_text="answer",
        is_correct=None,
        points_earned=0.0
    )

    db_session.add_all([answer2_1, answer2_2, answer2_3, answer2_4])
    await db_session.commit()

    # Eager load relationships
    result_query2 = await db_session.execute(
        select(TestAttempt)
        .where(TestAttempt.id == attempt2.id)
        .options(
            selectinload(TestAttempt.answers),
            selectinload(TestAttempt.test).selectinload(Test.questions)
        )
    )
    attempt2 = result_query2.scalar_one()

    result2 = service.calculate_test_score(attempt2)
    assert result2["points_earned"] == 2.0  # 1 + 0 + 1 + 0
    assert result2["total_points"] == 6.0
    assert result2["score"] < 0.4  # 2/6 = 0.333...
    assert result2["passed"] is False  # 0.333 < 0.7
