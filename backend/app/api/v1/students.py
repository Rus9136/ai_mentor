"""
Student API endpoints for test-taking workflow.

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
from app.api.dependencies import require_student, get_current_user_school_id, get_current_user
from app.models.user import User
from app.models.student import Student
from app.models.test import Test, Question, TestPurpose, DifficultyLevel
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.mastery import ParagraphMastery, ChapterMastery
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.repositories.test_attempt_repo import TestAttemptRepository
from app.repositories.paragraph_mastery_repo import ParagraphMasteryRepository
from app.repositories.chapter_mastery_repo import ChapterMasteryRepository
from app.services.grading_service import GradingService
from app.schemas.test_attempt import (
    TestAttemptCreate,
    TestAttemptSubmit,
    TestAttemptResponse,
    TestAttemptDetailResponse,
    TestAttemptAnswerResponse,
    AvailableTestResponse,
    StudentProgressResponse,
)
from app.schemas.mastery import (
    ChapterMasteryResponse,
    ChapterMasteryDetailResponse,
    MasteryOverviewResponse,
)
from app.schemas.question import QuestionResponse, QuestionResponseStudent
from app.schemas.test import TestResponse


router = APIRouter()
logger = logging.getLogger(__name__)


async def get_student_from_user(db: AsyncSession, user: User) -> Student:
    """
    Asynchronously fetch Student record from User.

    This is needed because accessing current_user.student triggers
    lazy loading which doesn't work in async context.

    Args:
        db: Database session
        user: Current authenticated user

    Returns:
        Student record

    Raises:
        HTTPException 400 if student record not found
    """
    result = await db.execute(
        select(Student).where(Student.user_id == user.id)
    )
    student = result.scalar_one_or_none()
    if not student:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Student record not found for this user"
        )
    return student


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

    Args:
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        chapter_id: Optional filter by chapter
        paragraph_id: Optional filter by paragraph
        test_purpose: Optional filter by test purpose
        difficulty: Optional filter by difficulty
        db: Database session

    Returns:
        List of available tests with metadata
    """
    # Get student record asynchronously (avoid lazy loading)
    student = await get_student_from_user(db, current_user)
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

    # Apply difficulty filter if provided (not in repository method)
    if difficulty:
        tests = [t for t in tests if t.difficulty == difficulty]

    # Get attempt statistics for each test
    attempt_repo = TestAttemptRepository(db)
    result = []

    for test in tests:
        # Count student's attempts for this test
        attempts = await attempt_repo.get_student_attempts(
            student_id=student_id,
            test_id=test.id,
            school_id=school_id
        )

        attempts_count = len(attempts)
        best_score = None

        # Calculate best score from completed attempts
        completed_attempts = [a for a in attempts if a.status == AttemptStatus.COMPLETED and a.score is not None]
        if completed_attempts:
            best_score = max(a.score for a in completed_attempts)

        # Count questions using direct COUNT query (avoid RLS issues with eager loading)
        from sqlalchemy import select, func
        from app.models.test import Question
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

    Args:
        test_id: Test ID to start
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        TestAttemptDetailResponse with questions (without correct answers)

    Raises:
        HTTPException 404: Test not found
        HTTPException 403: Test not available for this school
        HTTPException 400: Test is not active
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get test WITHOUT eager loading (avoid RLS issues)
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    # Check test is available for this school (global or school-specific)
    if test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Test not available for your school"
        )

    # Check test is active
    if not test.is_active:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Test is not available"
        )

    # Load questions (options will be loaded later when building response)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    questions_data = await question_repo.get_by_test(test_id, load_options=False)

    # Calculate attempt number (auto-increment)
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

    # Use pre-loaded questions_data from above (test.questions is list, not relationship at this point)
    questions_response = []
    for question in sorted(questions_data, key=lambda q: q.sort_order):
        # Load options for this question
        options = await option_repo.get_by_question(question.id)

        # Build QuestionResponseStudent from dict to avoid SQLAlchemy relationship access
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

    # Add questions to test_data
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
        answers=[]  # No answers yet
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

    Args:
        attempt_id: Test attempt ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        TestAttemptDetailResponse

    Raises:
        HTTPException 404: Attempt not found
        HTTPException 403: Access denied (ownership or tenant isolation)
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get attempt with ownership and tenant checks
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

    # Get attempt with answers and test data
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
        # Determine which question schema to use
        # Build from dict to avoid any potential SQLAlchemy relationship issues
        q = answer.question
        if attempt_with_data.status == AttemptStatus.IN_PROGRESS:
            # Don't show correct answers yet (student-safe schema)
            question_data = {
                "id": q.id,
                "test_id": q.test_id,
                "sort_order": q.sort_order,
                "question_type": q.question_type,
                "question_text": q.question_text,
                "points": q.points,
                "created_at": q.created_at,
                "updated_at": q.updated_at,
                "options": []  # Options would need to be loaded separately if needed
            }
        else:
            # Show correct answers (attempt completed)
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
                "options": []  # Options would need to be loaded separately if needed
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

    Args:
        attempt_id: Test attempt ID
        submission: Test answers (bulk submit)
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        TestAttemptDetailResponse with grading results and correct answers

    Raises:
        HTTPException 404: Attempt not found
        HTTPException 403: Access denied (ownership or tenant isolation)
        HTTPException 400: Attempt not in IN_PROGRESS status
        HTTPException 400: Answer count doesn't match question count
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get attempt with ownership and tenant checks
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

    # Check attempt status
    if attempt.status != AttemptStatus.IN_PROGRESS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot submit: attempt status is {attempt.status}, expected IN_PROGRESS"
        )

    # Get test WITHOUT eager loading (avoid RLS issues)
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(attempt.test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {attempt.test_id} not found"
        )

    # Load questions (options will be loaded when needed)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    questions_data = await question_repo.get_by_test(attempt.test_id, load_options=False)

    # Validate answer count matches question count
    if len(submission.answers) != len(questions_data):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Answer count mismatch: got {len(submission.answers)} answers, "
                f"expected {len(questions_data)} questions"
            )
        )

    # Create TestAttemptAnswer records
    question_map = {q.id: q for q in questions_data}

    for answer_submit in submission.answers:
        if answer_submit.question_id not in question_map:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid question_id: {answer_submit.question_id}"
            )

        # Create answer record
        answer = TestAttemptAnswer(
            attempt_id=attempt_id,
            question_id=answer_submit.question_id,
            selected_option_ids=answer_submit.selected_option_ids,
            answer_text=answer_submit.answer_text,
            answered_at=datetime.now(timezone.utc)
        )
        db.add(answer)

    # Commit answers
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

    # Build response with correct answers (attempt completed)
    test_data = TestResponse.model_validate(test).model_dump()

    # Add questions with correct answers to test_data
    questions_data = []
    for question in sorted(test.questions, key=lambda q: q.order):
        q_dict = QuestionResponse.model_validate(question).model_dump()
        questions_data.append(q_dict)
    test_data["questions"] = questions_data

    answers_data = []
    for answer in sorted(attempt_with_data.answers, key=lambda a: a.question.order):
        # Show correct answers (attempt completed)
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

    Args:
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        chapter_id: Optional filter by chapter
        db: Database session

    Returns:
        StudentProgressResponse with mastery statistics
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get all paragraph mastery records for student
    mastery_repo = ParagraphMasteryRepository(db)
    mastery_records = await mastery_repo.get_by_student(
        student_id=student_id,
        school_id=school_id
    )

    # Filter by chapter if provided
    if chapter_id:
        # Get paragraph IDs for this chapter
        result = await db.execute(
            select(Paragraph.id).where(
                Paragraph.chapter_id == chapter_id,
                Paragraph.is_deleted == False
            )
        )
        paragraph_ids = set(result.scalars().all())

        # Filter mastery records
        mastery_records = [m for m in mastery_records if m.paragraph_id in paragraph_ids]

        # Get chapter name
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()
        chapter_name = chapter.title if chapter else None
    else:
        chapter_name = None

    # Calculate statistics
    total_paragraphs = len(mastery_records)
    completed_paragraphs = sum(1 for m in mastery_records if m.is_completed)
    mastered_paragraphs = sum(1 for m in mastery_records if m.status == 'mastered')
    struggling_paragraphs = sum(1 for m in mastery_records if m.status == 'struggling')

    # Calculate average and best scores
    if mastery_records:
        average_score = sum(m.average_score or 0.0 for m in mastery_records) / len(mastery_records)
        best_score = max((m.best_score for m in mastery_records if m.best_score is not None), default=None)
    else:
        average_score = 0.0
        best_score = None

    # Get total attempts count
    result = await db.execute(
        select(func.count(TestAttempt.id)).where(
            TestAttempt.student_id == student_id,
            TestAttempt.school_id == school_id,
            TestAttempt.status == AttemptStatus.COMPLETED
        )
    )
    total_attempts = result.scalar() or 0

    # Build paragraphs data
    paragraphs_data = []
    for mastery in mastery_records:
        # Get paragraph info
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


@router.get("/mastery/chapter/{chapter_id}", response_model=ChapterMasteryResponse)
async def get_chapter_mastery(
    chapter_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapter mastery level (A/B/C grouping).

    Returns mastery record with:
    - A/B/C level and mastery_score (0-100)
    - Paragraph counters (total, completed, mastered, struggling)
    - Progress percentage
    - Summative test results (if taken)

    Args:
        chapter_id: Chapter ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        ChapterMasteryResponse with A/B/C mastery level

    Raises:
        HTTPException 404: Chapter mastery not found (student hasn't started chapter)
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get chapter mastery record
    mastery_repo = ChapterMasteryRepository(db)
    mastery = await mastery_repo.get_by_student_chapter(
        student_id=student_id,
        chapter_id=chapter_id
    )

    if not mastery:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter mastery not found for chapter {chapter_id}. Student hasn't started this chapter yet."
        )

    # Verify tenant isolation
    if mastery.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    logger.info(
        f"Student {student_id} retrieved chapter {chapter_id} mastery: "
        f"level={mastery.mastery_level}, score={mastery.mastery_score:.2f}"
    )

    return ChapterMasteryResponse.model_validate(mastery)


@router.get("/mastery/overview", response_model=MasteryOverviewResponse)
async def get_mastery_overview(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get mastery overview for all chapters.

    Returns:
    - List of all chapters with mastery data (A/B/C levels)
    - Aggregated statistics (level_a_count, level_b_count, level_c_count)
    - Average mastery score across all chapters

    Args:
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        MasteryOverviewResponse with all chapters and aggregated stats
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get all chapter mastery records for student
    mastery_repo = ChapterMasteryRepository(db)
    mastery_records = await mastery_repo.get_by_student(
        student_id=student_id,
        school_id=school_id
    )

    # Build chapters data with chapter info
    chapters_data = []
    for mastery in mastery_records:
        # Get chapter info
        chapter_result = await db.execute(
            select(Chapter).where(Chapter.id == mastery.chapter_id)
        )
        chapter = chapter_result.scalar_one_or_none()

        chapters_data.append(
            ChapterMasteryDetailResponse(
                id=mastery.id,
                student_id=mastery.student_id,
                chapter_id=mastery.chapter_id,
                total_paragraphs=mastery.total_paragraphs,
                completed_paragraphs=mastery.completed_paragraphs,
                mastered_paragraphs=mastery.mastered_paragraphs,
                struggling_paragraphs=mastery.struggling_paragraphs,
                mastery_level=mastery.mastery_level,
                mastery_score=mastery.mastery_score,
                progress_percentage=mastery.progress_percentage,
                summative_score=mastery.summative_score,
                summative_passed=mastery.summative_passed,
                last_updated_at=mastery.last_updated_at,
                chapter_title=chapter.title if chapter else None,
                chapter_order=chapter.order if chapter else None
            )
        )

    # Calculate aggregated stats
    total_chapters = len(mastery_records)
    level_a_count = sum(1 for m in mastery_records if m.mastery_level == 'A')
    level_b_count = sum(1 for m in mastery_records if m.mastery_level == 'B')
    level_c_count = sum(1 for m in mastery_records if m.mastery_level == 'C')

    # Calculate average mastery score
    if mastery_records:
        average_mastery_score = sum(m.mastery_score for m in mastery_records) / len(mastery_records)
    else:
        average_mastery_score = 0.0

    logger.info(
        f"Student {student_id} mastery overview: {total_chapters} chapters tracked, "
        f"A={level_a_count}, B={level_b_count}, C={level_c_count}, "
        f"avg_score={average_mastery_score:.2f}"
    )

    return MasteryOverviewResponse(
        student_id=student_id,
        chapters=chapters_data,
        total_chapters=total_chapters,
        average_mastery_score=round(average_mastery_score, 2),
        level_a_count=level_a_count,
        level_b_count=level_b_count,
        level_c_count=level_c_count
    )


# =============================================================================
# Content Browsing Endpoints (Textbooks, Chapters, Paragraphs)
# =============================================================================

from app.schemas.student_content import (
    StudentTextbookResponse,
    StudentTextbookProgress,
    StudentChapterResponse,
    StudentChapterProgress,
    StudentParagraphResponse,
    StudentParagraphDetailResponse,
    ParagraphRichContent,
    ParagraphNavigationContext,
)
from app.models.textbook import Textbook
from app.models.learning import StudentParagraph as StudentParagraphModel
from app.models.paragraph_content import ParagraphContent
from app.repositories.textbook_repo import TextbookRepository
from sqlalchemy.orm import selectinload


@router.get("/textbooks", response_model=List[StudentTextbookResponse])
async def get_student_textbooks(
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get available textbooks for student with progress.

    Returns global textbooks (school_id = NULL) and school-specific textbooks.
    Each textbook includes progress stats calculated from student's mastery data.

    Args:
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        List of textbooks with progress information
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id
    student_grade = student.grade_level

    # Get textbooks: global (school_id = NULL) OR school-specific
    textbook_repo = TextbookRepository(db)
    textbooks = await textbook_repo.get_by_school(school_id=school_id, include_global=True)

    # Filter active textbooks only
    textbooks = [t for t in textbooks if t.is_active and not t.is_deleted]

    # Optionally filter by student's grade level (uncomment if needed)
    # textbooks = [t for t in textbooks if t.grade_level == student_grade]

    result = []

    for textbook in textbooks:
        # Get chapters count
        chapters_result = await db.execute(
            select(func.count(Chapter.id)).where(
                Chapter.textbook_id == textbook.id,
                Chapter.is_deleted == False
            )
        )
        chapters_count = chapters_result.scalar() or 0

        # Get total paragraphs count
        paragraphs_result = await db.execute(
            select(func.count(Paragraph.id))
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                Chapter.is_deleted == False,
                Paragraph.is_deleted == False
            )
        )
        paragraphs_total = paragraphs_result.scalar() or 0

        # Get student's completed paragraphs for this textbook
        completed_result = await db.execute(
            select(func.count(ParagraphMastery.id))
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
        )
        paragraphs_completed = completed_result.scalar() or 0

        # Get completed chapters (all paragraphs completed)
        # A chapter is completed if all its paragraphs are completed by the student
        chapters_completed = 0
        chapter_ids_result = await db.execute(
            select(Chapter.id).where(
                Chapter.textbook_id == textbook.id,
                Chapter.is_deleted == False
            )
        )
        chapter_ids = chapter_ids_result.scalars().all()

        for chapter_id in chapter_ids:
            # Count paragraphs in chapter
            ch_para_total = await db.execute(
                select(func.count(Paragraph.id)).where(
                    Paragraph.chapter_id == chapter_id,
                    Paragraph.is_deleted == False
                )
            )
            ch_para_total_count = ch_para_total.scalar() or 0

            if ch_para_total_count == 0:
                continue

            # Count completed by student
            ch_para_completed = await db.execute(
                select(func.count(ParagraphMastery.id))
                .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
                .where(
                    Paragraph.chapter_id == chapter_id,
                    ParagraphMastery.student_id == student_id,
                    ParagraphMastery.is_completed == True
                )
            )
            ch_para_completed_count = ch_para_completed.scalar() or 0

            if ch_para_completed_count >= ch_para_total_count:
                chapters_completed += 1

        # Calculate percentage
        percentage = 0
        if paragraphs_total > 0:
            percentage = int((paragraphs_completed / paragraphs_total) * 100)

        # Get overall mastery level (average across chapters)
        mastery_result = await db.execute(
            select(func.avg(ChapterMastery.mastery_score))
            .join(Chapter, ChapterMastery.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                ChapterMastery.student_id == student_id
            )
        )
        avg_mastery_score = mastery_result.scalar()

        mastery_level = None
        if avg_mastery_score is not None:
            if avg_mastery_score >= 85:
                mastery_level = "A"
            elif avg_mastery_score >= 60:
                mastery_level = "B"
            else:
                mastery_level = "C"

        # Get last activity
        last_activity_result = await db.execute(
            select(func.max(ParagraphMastery.last_updated_at))
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .join(Chapter, Paragraph.chapter_id == Chapter.id)
            .where(
                Chapter.textbook_id == textbook.id,
                ParagraphMastery.student_id == student_id
            )
        )
        last_activity = last_activity_result.scalar()

        # Build response
        result.append(
            StudentTextbookResponse(
                id=textbook.id,
                title=textbook.title,
                subject=textbook.subject,
                grade_level=textbook.grade_level,
                description=textbook.description,
                is_global=textbook.school_id is None,
                progress=StudentTextbookProgress(
                    chapters_total=chapters_count,
                    chapters_completed=chapters_completed,
                    paragraphs_total=paragraphs_total,
                    paragraphs_completed=paragraphs_completed,
                    percentage=percentage
                ),
                mastery_level=mastery_level,
                last_activity=last_activity,
                author=textbook.author,
                chapters_count=chapters_count
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} textbooks")
    return result


@router.get("/textbooks/{textbook_id}/chapters", response_model=List[StudentChapterResponse])
async def get_textbook_chapters(
    textbook_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get chapters for a textbook with student's progress.

    Args:
        textbook_id: Textbook ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        List of chapters with progress and mastery information

    Raises:
        HTTPException 404: Textbook not found
        HTTPException 403: Access denied
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Verify textbook access
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    # Check access: global OR same school
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    # Get chapters ordered by order field
    chapters_result = await db.execute(
        select(Chapter).where(
            Chapter.textbook_id == textbook_id,
            Chapter.is_deleted == False
        ).order_by(Chapter.order)
    )
    chapters = chapters_result.scalars().all()

    result = []

    for idx, chapter in enumerate(chapters):
        # Get paragraphs count
        para_total_result = await db.execute(
            select(func.count(Paragraph.id)).where(
                Paragraph.chapter_id == chapter.id,
                Paragraph.is_deleted == False
            )
        )
        para_total = para_total_result.scalar() or 0

        # Get completed paragraphs
        para_completed_result = await db.execute(
            select(func.count(ParagraphMastery.id))
            .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
            .where(
                Paragraph.chapter_id == chapter.id,
                ParagraphMastery.student_id == student_id,
                ParagraphMastery.is_completed == True
            )
        )
        para_completed = para_completed_result.scalar() or 0

        # Calculate percentage
        percentage = 0
        if para_total > 0:
            percentage = int((para_completed / para_total) * 100)

        # Get chapter mastery
        mastery_result = await db.execute(
            select(ChapterMastery).where(
                ChapterMastery.chapter_id == chapter.id,
                ChapterMastery.student_id == student_id
            )
        )
        chapter_mastery = mastery_result.scalar_one_or_none()

        mastery_level = None
        mastery_score = None
        summative_passed = None

        if chapter_mastery:
            mastery_level = chapter_mastery.mastery_level
            mastery_score = chapter_mastery.mastery_score
            summative_passed = chapter_mastery.summative_passed

        # Determine chapter status
        if para_completed >= para_total and para_total > 0:
            chapter_status = "completed"
        elif para_completed > 0:
            chapter_status = "in_progress"
        else:
            # Check if previous chapter is completed (sequential unlock)
            if idx == 0:
                chapter_status = "not_started"
            else:
                prev_chapter = chapters[idx - 1]
                # Check if previous chapter is completed
                prev_para_total_result = await db.execute(
                    select(func.count(Paragraph.id)).where(
                        Paragraph.chapter_id == prev_chapter.id,
                        Paragraph.is_deleted == False
                    )
                )
                prev_para_total = prev_para_total_result.scalar() or 0

                prev_para_completed_result = await db.execute(
                    select(func.count(ParagraphMastery.id))
                    .join(Paragraph, ParagraphMastery.paragraph_id == Paragraph.id)
                    .where(
                        Paragraph.chapter_id == prev_chapter.id,
                        ParagraphMastery.student_id == student_id,
                        ParagraphMastery.is_completed == True
                    )
                )
                prev_para_completed = prev_para_completed_result.scalar() or 0

                if prev_para_completed >= prev_para_total and prev_para_total > 0:
                    chapter_status = "not_started"
                else:
                    chapter_status = "locked"

        # Check for summative test
        test_result = await db.execute(
            select(func.count(Test.id)).where(
                Test.chapter_id == chapter.id,
                Test.test_purpose == TestPurpose.SUMMATIVE,
                Test.is_active == True,
                Test.is_deleted == False
            )
        )
        has_summative_test = (test_result.scalar() or 0) > 0

        result.append(
            StudentChapterResponse(
                id=chapter.id,
                textbook_id=chapter.textbook_id,
                title=chapter.title,
                number=chapter.number,
                order=chapter.order,
                description=chapter.description,
                learning_objective=chapter.learning_objective,
                status=chapter_status,
                progress=StudentChapterProgress(
                    paragraphs_total=para_total,
                    paragraphs_completed=para_completed,
                    percentage=percentage
                ),
                mastery_level=mastery_level,
                mastery_score=mastery_score,
                has_summative_test=has_summative_test,
                summative_passed=summative_passed
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} chapters for textbook {textbook_id}")
    return result


@router.get("/chapters/{chapter_id}/paragraphs", response_model=List[StudentParagraphResponse])
async def get_chapter_paragraphs(
    chapter_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get paragraphs for a chapter with student's progress.

    Args:
        chapter_id: Chapter ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        List of paragraphs with status and practice info

    Raises:
        HTTPException 404: Chapter not found
        HTTPException 403: Access denied
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get chapter with textbook info
    chapter_result = await db.execute(
        select(Chapter)
        .options(selectinload(Chapter.textbook))
        .where(Chapter.id == chapter_id, Chapter.is_deleted == False)
    )
    chapter = chapter_result.scalar_one_or_none()

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Check textbook access
    textbook = chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    # Get paragraphs ordered by order
    paragraphs_result = await db.execute(
        select(Paragraph).where(
            Paragraph.chapter_id == chapter_id,
            Paragraph.is_deleted == False
        ).order_by(Paragraph.order)
    )
    paragraphs = paragraphs_result.scalars().all()

    result = []

    for para in paragraphs:
        # Get mastery info
        mastery_result = await db.execute(
            select(ParagraphMastery).where(
                ParagraphMastery.paragraph_id == para.id,
                ParagraphMastery.student_id == student_id
            )
        )
        mastery = mastery_result.scalar_one_or_none()

        # Determine status
        if mastery and mastery.is_completed:
            para_status = "completed"
        elif mastery:
            para_status = "in_progress"
        else:
            para_status = "not_started"

        practice_score = None
        if mastery and mastery.best_score is not None:
            practice_score = mastery.best_score

        # Estimate time (based on content length, ~200 words per minute)
        word_count = len(para.content.split()) if para.content else 0
        estimated_time = max(3, min(15, word_count // 200 + 3))  # 3-15 minutes

        # Check for practice test
        test_result = await db.execute(
            select(func.count(Test.id)).where(
                Test.paragraph_id == para.id,
                Test.test_purpose.in_([TestPurpose.FORMATIVE, TestPurpose.PRACTICE]),
                Test.is_active == True,
                Test.is_deleted == False
            )
        )
        has_practice = (test_result.scalar() or 0) > 0

        result.append(
            StudentParagraphResponse(
                id=para.id,
                chapter_id=para.chapter_id,
                title=para.title,
                number=para.number,
                order=para.order,
                summary=para.summary,
                status=para_status,
                estimated_time=estimated_time,
                has_practice=has_practice,
                practice_score=practice_score,
                learning_objective=para.learning_objective,
                key_terms=para.key_terms
            )
        )

    logger.info(f"Student {student_id} retrieved {len(result)} paragraphs for chapter {chapter_id}")
    return result


@router.get("/paragraphs/{paragraph_id}", response_model=StudentParagraphDetailResponse)
async def get_paragraph_detail(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get full paragraph content for learning.

    Args:
        paragraph_id: Paragraph ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Full paragraph with content and rich content availability flags

    Raises:
        HTTPException 404: Paragraph not found
        HTTPException 403: Access denied
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get paragraph with chapter and textbook
    para_result = await db.execute(
        select(Paragraph)
        .options(
            selectinload(Paragraph.chapter).selectinload(Chapter.textbook),
            selectinload(Paragraph.contents)
        )
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get mastery info
    mastery_result = await db.execute(
        select(ParagraphMastery).where(
            ParagraphMastery.paragraph_id == paragraph_id,
            ParagraphMastery.student_id == student_id
        )
    )
    mastery = mastery_result.scalar_one_or_none()

    # Determine status
    if mastery and mastery.is_completed:
        para_status = "completed"
    elif mastery:
        para_status = "in_progress"
    else:
        para_status = "not_started"

    # Check rich content availability (for any language)
    has_audio = False
    has_video = False
    has_slides = False
    has_cards = False

    for content in paragraph.contents:
        if content.audio_url:
            has_audio = True
        if content.video_url:
            has_video = True
        if content.slides_url:
            has_slides = True
        if content.cards:
            has_cards = True

    # Update last accessed (create or update StudentParagraph record)
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            last_accessed_at=datetime.now(timezone.utc)
        )
        db.add(student_para)
    else:
        student_para.last_accessed_at = datetime.now(timezone.utc)

    await db.commit()

    logger.info(f"Student {student_id} accessed paragraph {paragraph_id}")

    return StudentParagraphDetailResponse(
        id=paragraph.id,
        chapter_id=paragraph.chapter_id,
        title=paragraph.title,
        number=paragraph.number,
        order=paragraph.order,
        content=paragraph.content,
        summary=paragraph.summary,
        learning_objective=paragraph.learning_objective,
        lesson_objective=paragraph.lesson_objective,
        key_terms=paragraph.key_terms,
        questions=paragraph.questions,
        status=para_status,
        current_step=None,  # Could track learning step in future
        has_audio=has_audio,
        has_video=has_video,
        has_slides=has_slides,
        has_cards=has_cards,
        chapter_title=paragraph.chapter.title,
        textbook_title=textbook.title
    )


@router.get("/paragraphs/{paragraph_id}/content", response_model=ParagraphRichContent)
async def get_paragraph_rich_content(
    paragraph_id: int,
    language: str = Query("ru", description="Content language: ru or kk"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get rich content for a paragraph (audio, video, slides, cards).

    Args:
        paragraph_id: Paragraph ID
        language: Content language (ru or kk)
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Rich content with media URLs and flashcards

    Raises:
        HTTPException 404: Paragraph or content not found
        HTTPException 403: Access denied
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Validate language
    if language not in ("ru", "kk"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Language must be 'ru' or 'kk'"
        )

    # Get paragraph with chapter
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get content for requested language
    content_result = await db.execute(
        select(ParagraphContent).where(
            ParagraphContent.paragraph_id == paragraph_id,
            ParagraphContent.language == language
        )
    )
    content = content_result.scalar_one_or_none()

    # Build response (even if no content exists yet)
    if content:
        # Parse cards if they exist
        cards = None
        if content.cards:
            from app.schemas.student_content import FlashCard
            cards = [FlashCard(**card) for card in content.cards]

        return ParagraphRichContent(
            paragraph_id=paragraph_id,
            language=language,
            explain_text=content.explain_text,
            audio_url=content.audio_url,
            video_url=content.video_url,
            slides_url=content.slides_url,
            cards=cards,
            has_explain=content.explain_text is not None,
            has_audio=content.audio_url is not None,
            has_video=content.video_url is not None,
            has_slides=content.slides_url is not None,
            has_cards=content.cards is not None and len(content.cards) > 0
        )
    else:
        # Return empty content
        return ParagraphRichContent(
            paragraph_id=paragraph_id,
            language=language,
            explain_text=None,
            audio_url=None,
            video_url=None,
            slides_url=None,
            cards=None,
            has_explain=False,
            has_audio=False,
            has_video=False,
            has_slides=False,
            has_cards=False
        )


@router.get("/paragraphs/{paragraph_id}/navigation", response_model=ParagraphNavigationContext)
async def get_paragraph_navigation(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get navigation context for paragraph learning view.

    Includes previous/next paragraph IDs, chapter info, and position.

    Args:
        paragraph_id: Current paragraph ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Navigation context with previous/next paragraph info

    Raises:
        HTTPException 404: Paragraph not found
        HTTPException 403: Access denied
    """
    # Get paragraph with chapter and textbook
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    chapter = paragraph.chapter

    # Get all paragraphs in chapter ordered
    all_paras_result = await db.execute(
        select(Paragraph).where(
            Paragraph.chapter_id == chapter.id,
            Paragraph.is_deleted == False
        ).order_by(Paragraph.order)
    )
    all_paragraphs = all_paras_result.scalars().all()

    # Find current position and neighbors
    current_idx = None
    for idx, p in enumerate(all_paragraphs):
        if p.id == paragraph_id:
            current_idx = idx
            break

    previous_id = None
    next_id = None

    if current_idx is not None:
        if current_idx > 0:
            previous_id = all_paragraphs[current_idx - 1].id
        if current_idx < len(all_paragraphs) - 1:
            next_id = all_paragraphs[current_idx + 1].id

    return ParagraphNavigationContext(
        current_paragraph_id=paragraph_id,
        current_paragraph_number=paragraph.number,
        current_paragraph_title=paragraph.title,
        chapter_id=chapter.id,
        chapter_title=chapter.title,
        chapter_number=chapter.number,
        textbook_id=textbook.id,
        textbook_title=textbook.title,
        previous_paragraph_id=previous_id,
        next_paragraph_id=next_id,
        total_paragraphs_in_chapter=len(all_paragraphs),
        current_position_in_chapter=(current_idx or 0) + 1
    )


# =============================================================================
# Step Progress and Self-Assessment Endpoints
# =============================================================================

from app.schemas.embedded_question import (
    SelfAssessmentRequest,
    SelfAssessmentResponse,
    UpdateStepRequest,
    StepProgressResponse,
    ParagraphProgressResponse,
    EmbeddedQuestionForStudent,
    AnswerEmbeddedQuestionRequest,
    AnswerEmbeddedQuestionResponse,
)
from app.models.embedded_question import EmbeddedQuestion, StudentEmbeddedAnswer


@router.get("/paragraphs/{paragraph_id}/progress", response_model=ParagraphProgressResponse)
async def get_paragraph_progress(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get student's progress for a paragraph including step tracking.

    Args:
        paragraph_id: Paragraph ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Progress with current step, time spent, and embedded questions stats
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get paragraph to verify access
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get student's paragraph progress
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    # Determine available steps based on paragraph content
    available_steps = ["intro", "content"]

    # Check if paragraph has embedded questions (practice step)
    eq_count_result = await db.execute(
        select(func.count(EmbeddedQuestion.id)).where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            EmbeddedQuestion.is_active == True
        )
    )
    embedded_questions_total = eq_count_result.scalar() or 0

    if embedded_questions_total > 0:
        available_steps.append("practice")

    # Add summary step if paragraph has summary
    if paragraph.summary:
        available_steps.append("summary")

    # Get embedded questions answered by student
    answered_result = await db.execute(
        select(func.count(StudentEmbeddedAnswer.id))
        .join(EmbeddedQuestion, StudentEmbeddedAnswer.question_id == EmbeddedQuestion.id)
        .where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            StudentEmbeddedAnswer.student_id == student_id
        )
    )
    embedded_questions_answered = answered_result.scalar() or 0

    # Get correct answers count
    correct_result = await db.execute(
        select(func.count(StudentEmbeddedAnswer.id))
        .join(EmbeddedQuestion, StudentEmbeddedAnswer.question_id == EmbeddedQuestion.id)
        .where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            StudentEmbeddedAnswer.student_id == student_id,
            StudentEmbeddedAnswer.is_correct == True
        )
    )
    embedded_questions_correct = correct_result.scalar() or 0

    if student_para:
        return ParagraphProgressResponse(
            paragraph_id=paragraph_id,
            is_completed=student_para.is_completed,
            current_step=student_para.current_step or "intro",
            time_spent=student_para.time_spent,
            last_accessed_at=student_para.last_accessed_at,
            completed_at=student_para.completed_at,
            self_assessment=student_para.self_assessment,
            self_assessment_at=student_para.self_assessment_at,
            available_steps=available_steps,
            embedded_questions_total=embedded_questions_total,
            embedded_questions_answered=embedded_questions_answered,
            embedded_questions_correct=embedded_questions_correct
        )
    else:
        return ParagraphProgressResponse(
            paragraph_id=paragraph_id,
            is_completed=False,
            current_step="intro",
            time_spent=0,
            last_accessed_at=None,
            completed_at=None,
            self_assessment=None,
            self_assessment_at=None,
            available_steps=available_steps,
            embedded_questions_total=embedded_questions_total,
            embedded_questions_answered=embedded_questions_answered,
            embedded_questions_correct=embedded_questions_correct
        )


@router.post("/paragraphs/{paragraph_id}/progress", response_model=StepProgressResponse)
async def update_paragraph_progress(
    paragraph_id: int,
    request: UpdateStepRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student's progress step for a paragraph.

    Args:
        paragraph_id: Paragraph ID
        request: New step and optional time spent
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Updated progress with current step
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get paragraph to verify access
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get or create student's paragraph progress
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            current_step=request.step,
            time_spent=request.time_spent or 0,
            last_accessed_at=now
        )
        db.add(student_para)
    else:
        student_para.current_step = request.step
        student_para.last_accessed_at = now
        if request.time_spent:
            student_para.time_spent += request.time_spent

    # Mark as completed if step is 'completed'
    if request.step == "completed":
        student_para.is_completed = True
        student_para.completed_at = now

    await db.commit()
    await db.refresh(student_para)

    # Determine available steps
    available_steps = ["intro", "content"]
    eq_count_result = await db.execute(
        select(func.count(EmbeddedQuestion.id)).where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            EmbeddedQuestion.is_active == True
        )
    )
    if (eq_count_result.scalar() or 0) > 0:
        available_steps.append("practice")
    if paragraph.summary:
        available_steps.append("summary")

    logger.info(f"Student {student_id} updated paragraph {paragraph_id} progress to step '{request.step}'")

    return StepProgressResponse(
        paragraph_id=paragraph_id,
        current_step=student_para.current_step,
        is_completed=student_para.is_completed,
        time_spent=student_para.time_spent,
        available_steps=available_steps,
        self_assessment=student_para.self_assessment
    )


@router.post("/paragraphs/{paragraph_id}/self-assessment", response_model=SelfAssessmentResponse)
async def submit_self_assessment(
    paragraph_id: int,
    request: SelfAssessmentRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit self-assessment for a paragraph.

    Rating options:
    - understood: Всё понятно
    - questions: Есть вопросы
    - difficult: Сложно

    Args:
        paragraph_id: Paragraph ID
        request: Self-assessment rating
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Confirmation with timestamp
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get paragraph to verify access
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get or create student's paragraph progress
    student_para_result = await db.execute(
        select(StudentParagraphModel).where(
            StudentParagraphModel.paragraph_id == paragraph_id,
            StudentParagraphModel.student_id == student_id
        )
    )
    student_para = student_para_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if not student_para:
        student_para = StudentParagraphModel(
            student_id=student_id,
            paragraph_id=paragraph_id,
            school_id=school_id,
            self_assessment=request.rating,
            self_assessment_at=now,
            last_accessed_at=now
        )
        db.add(student_para)
    else:
        student_para.self_assessment = request.rating
        student_para.self_assessment_at = now
        student_para.last_accessed_at = now

    await db.commit()

    logger.info(f"Student {student_id} submitted self-assessment '{request.rating}' for paragraph {paragraph_id}")

    # Return appropriate message based on rating
    messages = {
        "understood": "Отлично! Продолжай в том же духе!",
        "questions": "Хорошо, попробуй повторить материал или задай вопрос.",
        "difficult": "Не переживай! Попробуй посмотреть материал в другом формате."
    }

    return SelfAssessmentResponse(
        paragraph_id=paragraph_id,
        rating=request.rating,
        recorded_at=now,
        message=messages.get(request.rating, "Оценка сохранена")
    )


# =============================================================================
# Embedded Questions Endpoints
# =============================================================================

@router.get("/paragraphs/{paragraph_id}/embedded-questions", response_model=List[EmbeddedQuestionForStudent])
async def get_embedded_questions(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get embedded questions for a paragraph (without correct answers).

    These are "Check yourself" questions shown during paragraph reading.

    Args:
        paragraph_id: Paragraph ID
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        List of questions without correct answer indicators
    """
    student = await get_student_from_user(db, current_user)

    # Get paragraph to verify access
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Check textbook access
    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    # Get active embedded questions
    questions_result = await db.execute(
        select(EmbeddedQuestion).where(
            EmbeddedQuestion.paragraph_id == paragraph_id,
            EmbeddedQuestion.is_active == True
        ).order_by(EmbeddedQuestion.sort_order)
    )
    questions = questions_result.scalars().all()

    # Convert to student-safe format (without is_correct)
    result = []
    for q in questions:
        result.append(EmbeddedQuestionForStudent.from_question(q))

    return result


@router.post("/embedded-questions/{question_id}/answer", response_model=AnswerEmbeddedQuestionResponse)
async def answer_embedded_question(
    question_id: int,
    request: AnswerEmbeddedQuestionRequest,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit answer to an embedded question.

    For single_choice/true_false: answer should be a string (option id or "true"/"false")
    For multiple_choice: answer should be a list of option ids

    Args:
        question_id: Embedded question ID
        request: Answer data
        current_user: Current authenticated student
        school_id: Student's school ID (from token)
        db: Database session

    Returns:
        Whether answer is correct, explanation, and correct answer
    """
    student = await get_student_from_user(db, current_user)
    student_id = student.id

    # Get question
    question_result = await db.execute(
        select(EmbeddedQuestion).where(
            EmbeddedQuestion.id == question_id,
            EmbeddedQuestion.is_active == True
        )
    )
    question = question_result.scalar_one_or_none()

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify access through paragraph -> chapter -> textbook
    para_result = await db.execute(
        select(Paragraph)
        .options(selectinload(Paragraph.chapter).selectinload(Chapter.textbook))
        .where(Paragraph.id == question.paragraph_id, Paragraph.is_deleted == False)
    )
    paragraph = para_result.scalar_one_or_none()

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Question's paragraph not found"
        )

    textbook = paragraph.chapter.textbook
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied"
        )

    # Check answer
    is_correct = question.check_answer(request.answer)

    # Get correct answer for response
    correct_answer = None
    if question.question_type == "true_false":
        correct_answer = question.correct_answer
    elif question.options:
        if question.question_type == "single_choice":
            for opt in question.options:
                if opt.get("is_correct"):
                    correct_answer = opt.get("id")
                    break
        else:  # multiple_choice
            correct_answer = [opt.get("id") for opt in question.options if opt.get("is_correct")]

    # Save or update student's answer
    existing_answer_result = await db.execute(
        select(StudentEmbeddedAnswer).where(
            StudentEmbeddedAnswer.student_id == student_id,
            StudentEmbeddedAnswer.question_id == question_id
        )
    )
    existing_answer = existing_answer_result.scalar_one_or_none()

    now = datetime.now(timezone.utc)

    if existing_answer:
        # Update existing answer
        existing_answer.is_correct = is_correct
        existing_answer.attempts_count += 1
        existing_answer.answered_at = now
        if isinstance(request.answer, list):
            existing_answer.selected_options = request.answer
            existing_answer.selected_answer = None
        else:
            existing_answer.selected_answer = str(request.answer)
            existing_answer.selected_options = None
        attempts_count = existing_answer.attempts_count
    else:
        # Create new answer
        new_answer = StudentEmbeddedAnswer(
            student_id=student_id,
            question_id=question_id,
            school_id=school_id,
            is_correct=is_correct,
            answered_at=now,
            attempts_count=1
        )
        if isinstance(request.answer, list):
            new_answer.selected_options = request.answer
        else:
            new_answer.selected_answer = str(request.answer)
        db.add(new_answer)
        attempts_count = 1

    await db.commit()

    logger.info(
        f"Student {student_id} answered embedded question {question_id}: "
        f"correct={is_correct}, attempts={attempts_count}"
    )

    return AnswerEmbeddedQuestionResponse(
        is_correct=is_correct,
        correct_answer=correct_answer,
        explanation=question.explanation,
        attempts_count=attempts_count
    )
