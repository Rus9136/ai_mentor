"""
Student Test-taking API endpoints.

This module provides endpoints for students to:
- View available tests (global + school-specific)
- Start a new test attempt
- Get current attempt details
- Submit test answers (triggers automatic grading)
- View their learning progress
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
)
from app.models.user import User
from app.models.test import Test, Question, TestPurpose, DifficultyLevel
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.mastery import ParagraphMastery
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.repositories.test_attempt_repo import TestAttemptRepository
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository
from app.services.grading_service import GradingService
from app.schemas.test_attempt import (
    TestAttemptSubmit,
    TestAttemptDetailResponse,
    TestAttemptAnswerResponse,
    AvailableTestResponse,
    StudentProgressResponse,
)
from app.schemas.question import QuestionResponse, QuestionResponseStudent
from app.schemas.test import TestResponse, TestQuestionAnswerRequest, TestAnswerResponse


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tests", response_model=List[AvailableTestResponse])
async def get_available_tests(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    chapter_id: Optional[int] = Query(None, description="Filter by chapter ID"),
    paragraph_id: Optional[int] = Query(None, description="Filter by paragraph ID"),
    test_purpose: Optional[TestPurpose] = Query(None, description="Filter by test purpose"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available tests for student.

    Returns both global tests (school_id = NULL) and school-specific tests.
    Includes metadata: question_count, attempts_count, best_score.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get available tests
    test_repo = TestRepository(db)
    tests = await test_repo.get_available_for_student(
        school_id=school_id,
        chapter_id=chapter_id,
        paragraph_id=paragraph_id,
        test_purpose=test_purpose,
        is_active_only=True
    )

    # Apply difficulty filter if provided
    if difficulty:
        tests = [t for t in tests if t.difficulty == difficulty]

    # Get attempt statistics for each test
    attempt_repo = TestAttemptRepository(db)
    result = []

    for test in tests:
        attempts = await attempt_repo.get_student_attempts(
            student_id=student_id,
            test_id=test.id,
            school_id=school_id
        )

        attempts_count = len(attempts)
        best_score = None

        completed_attempts = [a for a in attempts if a.status == AttemptStatus.COMPLETED and a.score is not None]
        if completed_attempts:
            best_score = max(a.score for a in completed_attempts)

        # Count questions
        question_count_result = await db.execute(
            select(func.count(Question.id)).where(
                Question.test_id == test.id,
                Question.is_deleted == False
            )
        )
        question_count = question_count_result.scalar() or 0

        result.append(
            AvailableTestResponse(
                id=test.id,
                title=test.title,
                description=test.description,
                test_purpose=test.test_purpose,
                difficulty=test.difficulty,
                time_limit=test.time_limit,
                passing_score=test.passing_score,
                is_active=test.is_active,
                chapter_id=test.chapter_id,
                paragraph_id=test.paragraph_id,
                school_id=test.school_id,
                question_count=question_count,
                attempts_count=attempts_count,
                best_score=best_score,
                created_at=test.created_at,
                updated_at=test.updated_at
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} available tests")
    return result


@router.post("/tests/{test_id}/start", response_model=TestAttemptDetailResponse)
async def start_test(
    test_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new test attempt.

    Creates a new TestAttempt with status IN_PROGRESS.
    Returns test details with questions WITHOUT correct answers (security).
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    # Get test WITHOUT eager loading
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test not available for your school"
        )

    if not test.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test is not available"
        )

    # Load questions
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    questions_data = await question_repo.get_by_test(test_id, load_options=False)

    # Calculate attempt number
    attempt_repo = TestAttemptRepository(db)
    attempt_count = await attempt_repo.count_attempts(
        student_id=student_id,
        test_id=test_id
    )
    attempt_number = attempt_count + 1

    # Create new attempt
    attempt = TestAttempt(
        student_id=student_id,
        test_id=test_id,
        school_id=school_id,
        attempt_number=attempt_number,
        status=AttemptStatus.IN_PROGRESS,
        started_at=datetime.now(timezone.utc)
    )

    attempt = await attempt_repo.create(attempt)

    logger.info(
        f"Student {student_id} started test {test_id}, "
        f"attempt #{attempt_number} (id={attempt.id})"
    )

    # Build response with QuestionResponseStudent (WITHOUT correct answers)
    test_data = TestResponse.model_validate(test).model_dump()

    questions_response = []
    for question in sorted(questions_data, key=lambda q: q.sort_order):
        options = await option_repo.get_by_question(question.id)

        q_dict = {
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
        }
        q_response = QuestionResponseStudent(**q_dict)
        questions_response.append(q_response.model_dump())

    test_data["questions"] = questions_response

    return TestAttemptDetailResponse(
        id=attempt.id,
        student_id=attempt.student_id,
        test_id=attempt.test_id,
        school_id=attempt.school_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=None,
        score=None,
        points_earned=None,
        total_points=None,
        passed=None,
        time_spent=None,
        created_at=attempt.created_at,
        updated_at=attempt.updated_at,
        test=test_data,
        answers=[]
    )


@router.get("/attempts/{attempt_id}", response_model=TestAttemptDetailResponse)
async def get_attempt(
    attempt_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get test attempt details.

    Returns attempt with questions:
    - If IN_PROGRESS: questions WITHOUT correct answers
    - If COMPLETED: questions WITH correct answers
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    attempt_repo = TestAttemptRepository(db)
    attempt = await attempt_repo.get_by_id(
        attempt_id=attempt_id,
        student_id=student_id,
        school_id=school_id
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test attempt {attempt_id} not found or access denied"
        )

    attempt_with_data = await attempt_repo.get_with_answers(attempt_id)

    if not attempt_with_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test attempt {attempt_id} not found"
        )

    # Build test data
    test = attempt_with_data.test
    test_data = TestResponse.model_validate(test).model_dump()

    # Build answers data with appropriate question schema
    answers_data = []
    for answer in sorted(attempt_with_data.answers, key=lambda a: a.question.sort_order):
        q = answer.question
        if attempt_with_data.status == AttemptStatus.IN_PROGRESS:
            question_data = {
                "id": q.id,
                "test_id": q.test_id,
                "sort_order": q.sort_order,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "points": q.points,
                "created_at": q.created_at,
                "updated_at": q.updated_at,
                "options": []
            }
        else:
            question_data = {
                "id": q.id,
                "test_id": q.test_id,
                "sort_order": q.sort_order,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "explanation": q.explanation,
                "points": q.points,
                "created_at": q.created_at,
                "updated_at": q.updated_at,
                "deleted_at": q.deleted_at,
                "is_deleted": q.is_deleted,
                "options": []
            }

        answer_dict = TestAttemptAnswerResponse(
            id=answer.id,
            attempt_id=answer.attempt_id,
            question_id=answer.question_id,
            selected_option_ids=answer.selected_option_ids,
            answer_text=answer.answer_text,
            is_correct=answer.is_correct,
            points_earned=answer.points_earned,
            answered_at=answer.answered_at,
            created_at=answer.created_at,
            updated_at=answer.updated_at,
            question=question_data
        )
        answers_data.append(answer_dict)

    return TestAttemptDetailResponse(
        id=attempt_with_data.id,
        student_id=attempt_with_data.student_id,
        test_id=attempt_with_data.test_id,
        school_id=attempt_with_data.school_id,
        attempt_number=attempt_with_data.attempt_number,
        status=attempt_with_data.status,
        started_at=attempt_with_data.started_at,
        completed_at=attempt_with_data.completed_at,
        score=attempt_with_data.score,
        points_earned=attempt_with_data.points_earned,
        total_points=attempt_with_data.total_points,
        passed=attempt_with_data.passed,
        time_spent=attempt_with_data.time_spent,
        created_at=attempt_with_data.created_at,
        updated_at=attempt_with_data.updated_at,
        test=test_data,
        answers=answers_data
    )


@router.post("/attempts/{attempt_id}/submit", response_model=TestAttemptDetailResponse)
async def submit_test(
    attempt_id: int,
    submission: TestAttemptSubmit,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit test answers and complete the attempt.

    Creates TestAttemptAnswer records, triggers automatic grading,
    and updates ParagraphMastery if test_purpose is FORMATIVE or SUMMATIVE.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    attempt_repo = TestAttemptRepository(db)
    attempt = await attempt_repo.get_by_id(
        attempt_id=attempt_id,
        student_id=student_id,
        school_id=school_id
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test attempt {attempt_id} not found or access denied"
        )

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit: attempt status is {attempt.status}, expected IN_PROGRESS"
        )

    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(attempt.test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {attempt.test_id} not found"
        )

    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    questions_data = await question_repo.get_by_test(attempt.test_id, load_options=False)

    if len(submission.answers) != len(questions_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Answer count mismatch: got {len(submission.answers)} answers, "
                f"expected {len(questions_data)} questions"
            )
        )

    question_map = {q.id: q for q in questions_data}

    for answer_submit in submission.answers:
        if answer_submit.question_id not in question_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid question_id: {answer_submit.question_id}"
            )

        answer = TestAttemptAnswer(
            attempt_id=attempt_id,
            question_id=answer_submit.question_id,
            selected_option_ids=answer_submit.selected_option_ids,
            answer_text=answer_submit.answer_text,
            answered_at=datetime.now(timezone.utc)
        )
        db.add(answer)

    await db.commit()

    logger.info(
        f"Student {student_id} submitted {len(submission.answers)} answers "
        f"for attempt {attempt_id}"
    )

    # Trigger automatic grading
    grading_service = GradingService(db)
    graded_attempt = await grading_service.grade_attempt(
        attempt_id=attempt_id,
        student_id=student_id,
        school_id=school_id
    )

    logger.info(
        f"Attempt {attempt_id} graded: score={graded_attempt.score}, "
        f"passed={graded_attempt.passed}"
    )

    # Get updated attempt with all data
    attempt_with_data = await attempt_repo.get_with_answers(attempt_id)

    test_data = TestResponse.model_validate(test).model_dump()

    questions_data_response = []
    for question in sorted(test.questions, key=lambda q: q.order):
        q_dict = QuestionResponse.model_validate(question).model_dump()
        questions_data_response.append(q_dict)
    test_data["questions"] = questions_data_response

    answers_data = []
    for answer in sorted(attempt_with_data.answers, key=lambda a: a.question.order):
        question_data = QuestionResponse.model_validate(answer.question).model_dump()

        answer_dict = TestAttemptAnswerResponse(
            id=answer.id,
            attempt_id=answer.attempt_id,
            question_id=answer.question_id,
            selected_option_ids=answer.selected_option_ids,
            answer_text=answer.answer_text,
            is_correct=answer.is_correct,
            points_earned=answer.points_earned,
            answered_at=answer.answered_at,
            created_at=answer.created_at,
            updated_at=answer.updated_at,
            question=question_data
        )
        answers_data.append(answer_dict)

    return TestAttemptDetailResponse(
        id=attempt_with_data.id,
        student_id=attempt_with_data.student_id,
        test_id=attempt_with_data.test_id,
        school_id=attempt_with_data.school_id,
        attempt_number=attempt_with_data.attempt_number,
        status=attempt_with_data.status,
        started_at=attempt_with_data.started_at,
        completed_at=attempt_with_data.completed_at,
        score=attempt_with_data.score,
        points_earned=attempt_with_data.points_earned,
        total_points=attempt_with_data.total_points,
        passed=attempt_with_data.passed,
        time_spent=attempt_with_data.time_spent,
        created_at=attempt_with_data.created_at,
        updated_at=attempt_with_data.updated_at,
        test=test_data,
        answers=answers_data
    )


@router.post("/attempts/{attempt_id}/answer", response_model=TestAnswerResponse)
async def answer_test_question(
    attempt_id: int,
    answer_request: TestQuestionAnswerRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit answer for a single question in test attempt.

    Returns immediate feedback with is_correct, correct_option_ids, and explanation.
    This endpoint is used for chat-like quiz interface where feedback is shown
    after each answer.

    Does NOT complete the attempt - allows answering questions one by one.
    The attempt is auto-completed when the last question is answered.
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    attempt_repo = TestAttemptRepository(db)
    attempt = await attempt_repo.get_by_id(
        attempt_id=attempt_id,
        student_id=student_id,
        school_id=school_id
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test attempt {attempt_id} not found or access denied"
        )

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot answer: attempt status is {attempt.status}, expected IN_PROGRESS"
        )

    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    question = await question_repo.get_by_id(answer_request.question_id)

    if not question or question.test_id != attempt.test_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question {answer_request.question_id} not found in this test"
        )

    # Check if already answered
    existing_answer_result = await db.execute(
        select(TestAttemptAnswer).where(
            TestAttemptAnswer.attempt_id == attempt_id,
            TestAttemptAnswer.question_id == answer_request.question_id
        )
    )
    existing_answer = existing_answer_result.scalar_one_or_none()

    if existing_answer:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Question {answer_request.question_id} already answered in this attempt"
        )

    options = await option_repo.get_by_question(answer_request.question_id)

    correct_option_ids = [opt.id for opt in options if opt.is_correct]

    selected_set = set(answer_request.selected_option_ids)
    correct_set = set(correct_option_ids)
    is_correct = selected_set == correct_set

    points_earned = question.points if is_correct else 0.0

    answer = TestAttemptAnswer(
        attempt_id=attempt_id,
        question_id=answer_request.question_id,
        selected_option_ids=answer_request.selected_option_ids,
        is_correct=is_correct,
        points_earned=points_earned,
        answered_at=datetime.now(timezone.utc)
    )
    db.add(answer)
    await db.commit()

    # Count total and answered questions
    total_questions_result = await db.execute(
        select(func.count(Question.id)).where(
            Question.test_id == attempt.test_id,
            Question.is_deleted == False
        )
    )
    total_questions = total_questions_result.scalar() or 0

    answered_count_result = await db.execute(
        select(func.count(TestAttemptAnswer.id)).where(
            TestAttemptAnswer.attempt_id == attempt_id
        )
    )
    answered_count = answered_count_result.scalar() or 0

    logger.info(
        f"Student {student_id} answered question {answer_request.question_id} "
        f"in attempt {attempt_id}: correct={is_correct}, points={points_earned}, "
        f"progress={answered_count}/{total_questions}"
    )

    # Auto-complete when all questions answered
    is_test_complete = False
    test_score = None
    test_passed = None

    if answered_count >= total_questions and total_questions > 0:
        logger.info(f"All questions answered, auto-completing attempt {attempt_id}")

        grading_service = GradingService(db)
        graded_attempt = await grading_service.grade_attempt(
            attempt_id=attempt_id,
            student_id=student_id,
            school_id=school_id
        )

        is_test_complete = True
        test_score = graded_attempt.score
        test_passed = graded_attempt.passed

        logger.info(
            f"Attempt {attempt_id} auto-completed: "
            f"score={test_score:.2f}, passed={test_passed}"
        )

    return TestAnswerResponse(
        question_id=answer_request.question_id,
        is_correct=is_correct,
        correct_option_ids=correct_option_ids,
        explanation=question.explanation,
        points_earned=points_earned,
        answered_count=answered_count,
        total_questions=total_questions,
        is_test_complete=is_test_complete,
        test_score=test_score,
        test_passed=test_passed
    )


@router.post("/attempts/{attempt_id}/complete", deprecated=True)
async def complete_test_attempt(
    attempt_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    [DEPRECATED] Complete a test attempt after all questions have been answered.

    This endpoint is deprecated. The /answer endpoint now auto-completes the test
    when the last question is answered. Use /answer and check is_test_complete in response.
    """
    logger.warning(
        f"Deprecated endpoint /complete called for attempt {attempt_id}. "
        "Use /answer with is_test_complete response field instead."
    )
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    attempt_repo = TestAttemptRepository(db)
    attempt = await attempt_repo.get_by_id(
        attempt_id=attempt_id,
        student_id=student_id,
        school_id=school_id
    )

    if not attempt:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test attempt {attempt_id} not found or access denied"
        )

    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot complete: attempt status is {attempt.status}, expected IN_PROGRESS"
        )

    question_repo = QuestionRepository(db)
    questions = await question_repo.get_by_test(attempt.test_id, load_options=False)
    total_questions = len(questions)

    answered_count_result = await db.execute(
        select(func.count(TestAttemptAnswer.id)).where(
            TestAttemptAnswer.attempt_id == attempt_id
        )
    )
    answered_count = answered_count_result.scalar() or 0

    if answered_count < total_questions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Not all questions answered: {answered_count}/{total_questions}"
        )

    logger.info(
        f"Student {student_id} completing attempt {attempt_id} "
        f"with {answered_count} answers"
    )

    grading_service = GradingService(db)
    graded_attempt = await grading_service.grade_attempt(
        attempt_id=attempt_id,
        student_id=student_id,
        school_id=school_id
    )

    logger.info(
        f"Attempt {attempt_id} graded: score={graded_attempt.score}, "
        f"passed={graded_attempt.passed}"
    )

    attempt_with_data = await attempt_repo.get_with_answers(attempt_id)

    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(attempt.test_id, load_questions=True)

    test_data = TestResponse.model_validate(test).model_dump()

    questions_data = []
    for question in sorted(test.questions, key=lambda q: q.sort_order):
        q_dict = QuestionResponse.model_validate(question).model_dump()
        questions_data.append(q_dict)
    test_data["questions"] = questions_data

    answers_data = []
    for answer in attempt_with_data.answers:
        question = next((q for q in test.questions if q.id == answer.question_id), None)
        if question:
            question_data = QuestionResponse.model_validate(question).model_dump()
            answer_dict = TestAttemptAnswerResponse(
                id=answer.id,
                attempt_id=answer.attempt_id,
                question_id=answer.question_id,
                selected_option_ids=answer.selected_option_ids,
                answer_text=answer.answer_text,
                is_correct=answer.is_correct,
                points_earned=answer.points_earned,
                answered_at=answer.answered_at,
                created_at=answer.created_at,
                updated_at=answer.updated_at,
                question=question_data
            )
            answers_data.append(answer_dict)

    answers_data.sort(key=lambda a: next((q.sort_order for q in test.questions if q.id == a.question_id), 0))

    return TestAttemptDetailResponse(
        id=attempt_with_data.id,
        student_id=attempt_with_data.student_id,
        test_id=attempt_with_data.test_id,
        school_id=attempt_with_data.school_id,
        attempt_number=attempt_with_data.attempt_number,
        status=attempt_with_data.status,
        started_at=attempt_with_data.started_at,
        completed_at=attempt_with_data.completed_at,
        score=attempt_with_data.score,
        points_earned=attempt_with_data.points_earned,
        total_points=attempt_with_data.total_points,
        passed=attempt_with_data.passed,
        time_spent=attempt_with_data.time_spent,
        created_at=attempt_with_data.created_at,
        updated_at=attempt_with_data.updated_at,
        test=test_data,
        answers=answers_data
    )


@router.get("/progress", response_model=StudentProgressResponse)
async def get_student_progress(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    chapter_id: Optional[int] = Query(None, description="Filter by chapter ID"),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student learning progress summary.

    Returns paragraph-level mastery statistics:
    - Total paragraphs
    - Completed paragraphs
    - Mastered paragraphs (status = 'mastered')
    - Struggling paragraphs (status = 'struggling')
    - Average and best scores
    """
    student = await get_student_from_user(current_user, db)
    student_id = student.id

    mastery_repo = ParagraphMasteryRepository(db)
    mastery_records = await mastery_repo.get_by_student(
        student_id=student_id,
        school_id=school_id
    )

    chapter_name = None
    if chapter_id:
        result = await db.execute(
            select(Paragraph.id).where(
                Paragraph.chapter_id == chapter_id,
                Paragraph.is_deleted == False
            )
        )
        paragraph_ids = set(result.scalars().all())
        mastery_records = [m for m in mastery_records if m.paragraph_id in paragraph_ids]

        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        chapter_name = chapter.title if chapter else None

    total_paragraphs = len(mastery_records)
    completed_paragraphs = sum(1 for m in mastery_records if m.is_completed)
    mastered_paragraphs = sum(1 for m in mastery_records if m.status == 'mastered')
    struggling_paragraphs = sum(1 for m in mastery_records if m.status == 'struggling')

    if mastery_records:
        average_score = sum(m.average_score or 0.0 for m in mastery_records) / len(mastery_records)
        best_score = max((m.best_score for m in mastery_records if m.best_score is not None), default=None)
    else:
        average_score = 0.0
        best_score = None

    result = await db.execute(
        select(func.count(TestAttempt.id)).where(
            TestAttempt.student_id == student_id,
            TestAttempt.school_id == school_id,
            TestAttempt.status == AttemptStatus.COMPLETED
        )
    )
    total_attempts = result.scalar() or 0

    paragraphs_data = []
    for mastery in mastery_records:
        paragraph_result = await db.execute(
            select(Paragraph).where(Paragraph.id == mastery.paragraph_id)
        )
        paragraph = paragraph_result.scalar_one_or_none()

        paragraphs_data.append({
            "paragraph_id": mastery.paragraph_id,
            "paragraph_title": paragraph.title if paragraph else None,
            "paragraph_number": paragraph.number if paragraph else None,
            "status": mastery.status,
            "average_score": mastery.average_score,
            "best_score": mastery.best_score,
            "is_completed": mastery.is_completed,
            "attempts_count": mastery.attempts_count,
            "time_spent": mastery.time_spent
        })

    logger.info(
        f"Student {student_id} progress: {mastered_paragraphs}/{total_paragraphs} mastered, "
        f"avg_score={average_score:.2f}"
    )

    return StudentProgressResponse(
        chapter_id=chapter_id,
        chapter_name=chapter_name,
        total_paragraphs=total_paragraphs,
        completed_paragraphs=completed_paragraphs,
        mastered_paragraphs=mastered_paragraphs,
        struggling_paragraphs=struggling_paragraphs,
        average_score=average_score,
        best_score=best_score,
        total_attempts=total_attempts,
        paragraphs=paragraphs_data
    )
