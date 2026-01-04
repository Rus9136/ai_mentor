"""
Student Test-taking API endpoints.

This module provides endpoints for students to:
- View available tests (global + school-specific)
- Start a new test attempt
- Get current attempt details
- Submit test answers (triggers automatic grading)
- Answer questions one by one with immediate feedback
"""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    get_current_user_school_id,
    get_student_from_user,
    get_test_taking_service,
)
from app.models.student import Student
from app.models.test import TestPurpose, DifficultyLevel
from app.services.grading_service import GradingService
from app.services.test_taking_service import TestTakingService
from app.schemas.test_attempt import (
    TestAttemptSubmit,
    TestAttemptDetailResponse,
    TestAttemptAnswerResponse,
    AvailableTestResponse,
)
from app.schemas.question import QuestionResponse, QuestionResponseStudent
from app.schemas.test import TestResponse, TestQuestionAnswerRequest, TestAnswerResponse


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get("/tests", response_model=List[AvailableTestResponse])
async def get_available_tests(
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    chapter_id: Optional[int] = Query(None, description="Filter by chapter ID"),
    paragraph_id: Optional[int] = Query(None, description="Filter by paragraph ID"),
    test_purpose: Optional[TestPurpose] = Query(None, description="Filter by test purpose"),
    difficulty: Optional[DifficultyLevel] = Query(None, description="Filter by difficulty"),
    service: TestTakingService = Depends(get_test_taking_service)
):
    """
    Get available tests for student.

    Returns both global tests (school_id = NULL) and school-specific tests.
    Includes metadata: question_count, attempts_count, best_score.
    """
    tests_data = await service.get_available_tests(
        school_id=school_id,
        student_id=student.id,
        chapter_id=chapter_id,
        paragraph_id=paragraph_id,
        test_purpose=test_purpose,
        difficulty=difficulty
    )

    result = []
    for item in tests_data:
        test = item["test"]
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
                question_count=item["question_count"],
                attempts_count=item["attempts_count"],
                best_score=item["best_score"],
                created_at=test.created_at,
                updated_at=test.updated_at
            )
        )

    return result


@router.post("/tests/{test_id}/start", response_model=TestAttemptDetailResponse)
async def start_test(
    test_id: int,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: TestTakingService = Depends(get_test_taking_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Start a new test attempt.

    Creates a new TestAttempt with status IN_PROGRESS.
    Returns test details with questions WITHOUT correct answers (security).
    """
    try:
        result = await service.start_test(
            student_id=student.id,
            test_id=test_id,
            school_id=school_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    await db.commit()

    attempt = result["attempt"]
    test = result["test"]
    questions = result["questions"]

    # Build response
    test_data = TestResponse.model_validate(test).model_dump()
    test_data["questions"] = [
        QuestionResponseStudent(**q).model_dump() for q in questions
    ]

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
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: TestTakingService = Depends(get_test_taking_service)
):
    """
    Get test attempt details.

    Returns attempt with questions:
    - If IN_PROGRESS: questions WITHOUT correct answers
    - If COMPLETED: questions WITH correct answers
    """
    try:
        result = await service.get_attempt_details(
            attempt_id=attempt_id,
            student_id=student.id,
            school_id=school_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )

    attempt = result["attempt"]
    test = result["test"]
    answers = result["answers"]

    # Build test data
    test_data = TestResponse.model_validate(test).model_dump()

    # Build answers data
    answers_data = [
        TestAttemptAnswerResponse(**answer) for answer in answers
    ]

    return TestAttemptDetailResponse(
        id=attempt.id,
        student_id=attempt.student_id,
        test_id=attempt.test_id,
        school_id=attempt.school_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        score=attempt.score,
        points_earned=attempt.points_earned,
        total_points=attempt.total_points,
        passed=attempt.passed,
        time_spent=attempt.time_spent,
        created_at=attempt.created_at,
        updated_at=attempt.updated_at,
        test=test_data,
        answers=answers_data
    )


@router.post("/attempts/{attempt_id}/submit", response_model=TestAttemptDetailResponse)
async def submit_test(
    attempt_id: int,
    submission: TestAttemptSubmit,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: TestTakingService = Depends(get_test_taking_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit test answers and complete the attempt.

    Creates TestAttemptAnswer records, triggers automatic grading,
    and updates ParagraphMastery if test_purpose is FORMATIVE or SUMMATIVE.
    """
    # Prepare answers data
    answers_data = [
        {
            "question_id": a.question_id,
            "selected_option_ids": a.selected_option_ids,
            "answer_text": a.answer_text
        }
        for a in submission.answers
    ]

    try:
        await service.submit_all_answers(
            attempt_id=attempt_id,
            answers=answers_data,
            student_id=student.id,
            school_id=school_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Commit answers first
    await db.commit()

    # Trigger grading (GradingService does its own commit)
    grading_service = GradingService(db)
    graded_attempt = await grading_service.grade_attempt(
        attempt_id=attempt_id,
        student_id=student.id,
        school_id=school_id
    )

    logger.info(
        f"Attempt {attempt_id} graded: score={graded_attempt.score}, "
        f"passed={graded_attempt.passed}"
    )

    # Get updated details
    result = await service.get_attempt_details(
        attempt_id=attempt_id,
        student_id=student.id,
        school_id=school_id
    )

    attempt = result["attempt"]
    test = result["test"]
    answers = result["answers"]

    test_data = TestResponse.model_validate(test).model_dump()
    answers_data = [TestAttemptAnswerResponse(**answer) for answer in answers]

    return TestAttemptDetailResponse(
        id=attempt.id,
        student_id=attempt.student_id,
        test_id=attempt.test_id,
        school_id=attempt.school_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        score=attempt.score,
        points_earned=attempt.points_earned,
        total_points=attempt.total_points,
        passed=attempt.passed,
        time_spent=attempt.time_spent,
        created_at=attempt.created_at,
        updated_at=attempt.updated_at,
        test=test_data,
        answers=answers_data
    )


@router.post("/attempts/{attempt_id}/answer", response_model=TestAnswerResponse)
async def answer_test_question(
    attempt_id: int,
    answer_request: TestQuestionAnswerRequest,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: TestTakingService = Depends(get_test_taking_service),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit answer for a single question in test attempt.

    Returns immediate feedback with is_correct, correct_option_ids, and explanation.
    The attempt is auto-completed when the last question is answered.
    """
    try:
        result = await service.answer_question(
            attempt_id=attempt_id,
            question_id=answer_request.question_id,
            selected_option_ids=answer_request.selected_option_ids,
            student_id=student.id,
            school_id=school_id
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Commit answer
    await db.commit()

    # Auto-complete if last question
    is_test_complete = False
    test_score = None
    test_passed = None

    if result["is_last_question"]:
        logger.info(f"All questions answered, auto-completing attempt {attempt_id}")

        grading_service = GradingService(db)
        graded_attempt = await grading_service.grade_attempt(
            attempt_id=attempt_id,
            student_id=student.id,
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
        question_id=result["question_id"],
        is_correct=result["is_correct"],
        correct_option_ids=result["correct_option_ids"],
        explanation=result["explanation"],
        points_earned=result["points_earned"],
        answered_count=result["answered_count"],
        total_questions=result["total_questions"],
        is_test_complete=is_test_complete,
        test_score=test_score,
        test_passed=test_passed
    )


@router.post("/attempts/{attempt_id}/complete", deprecated=True)
async def complete_test_attempt(
    attempt_id: int,
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: TestTakingService = Depends(get_test_taking_service),
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

    # Just trigger grading
    grading_service = GradingService(db)
    try:
        graded_attempt = await grading_service.grade_attempt(
            attempt_id=attempt_id,
            student_id=student.id,
            school_id=school_id
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    logger.info(
        f"Attempt {attempt_id} graded: score={graded_attempt.score}, "
        f"passed={graded_attempt.passed}"
    )

    # Get updated details
    result = await service.get_attempt_details(
        attempt_id=attempt_id,
        student_id=student.id,
        school_id=school_id
    )

    attempt = result["attempt"]
    test = result["test"]
    answers = result["answers"]

    test_data = TestResponse.model_validate(test).model_dump()
    answers_data = [TestAttemptAnswerResponse(**answer) for answer in answers]

    return TestAttemptDetailResponse(
        id=attempt.id,
        student_id=attempt.student_id,
        test_id=attempt.test_id,
        school_id=attempt.school_id,
        attempt_number=attempt.attempt_number,
        status=attempt.status,
        started_at=attempt.started_at,
        completed_at=attempt.completed_at,
        score=attempt.score,
        points_earned=attempt.points_earned,
        total_points=attempt.total_points,
        passed=attempt.passed,
        time_spent=attempt.time_spent,
        created_at=attempt.created_at,
        updated_at=attempt.updated_at,
        test=test_data,
        answers=answers_data
    )
