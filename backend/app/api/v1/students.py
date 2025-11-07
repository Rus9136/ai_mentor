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
from app.models.test import Test, Question, TestPurpose, DifficultyLevel
from app.models.test_attempt import TestAttempt, TestAttemptAnswer, AttemptStatus
from app.models.mastery import ParagraphMastery
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.repositories.test_repo import TestRepository
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
    # Get student ID
    student_id = current_user.student.id

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

        # Count questions (load if not already loaded)
        if not test.questions:
            test_with_questions = await test_repo.get_by_id(test.id, load_questions=True)
            question_count = len(test_with_questions.questions) if test_with_questions else 0
        else:
            question_count = len(test.questions)

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
    student_id = current_user.student.id

    # Get test with questions
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id, load_questions=True)

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

    questions_data = []
    for question in sorted(test.questions, key=lambda q: q.order):
        # Use QuestionResponseStudent - no is_correct, no explanation
        q_dict = QuestionResponseStudent.model_validate(question).model_dump()
        questions_data.append(q_dict)

    # Add questions to test_data
    test_data["questions"] = questions_data

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
    student_id = current_user.student.id

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
    for answer in sorted(attempt_with_data.answers, key=lambda a: a.question.order):
        # Determine which question schema to use
        if attempt_with_data.status == AttemptStatus.IN_PROGRESS:
            # Don't show correct answers yet
            question_data = QuestionResponseStudent.model_validate(answer.question).model_dump()
        else:
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
    student_id = current_user.student.id

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

    # Get test with questions
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(attempt.test_id, load_questions=True)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {attempt.test_id} not found"
        )

    # Validate answer count matches question count
    if len(submission.answers) != len(test.questions):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Answer count mismatch: got {len(submission.answers)} answers, "
                f"expected {len(test.questions)} questions"
            )
        )

    # Create TestAttemptAnswer records
    question_map = {q.id: q for q in test.questions}

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
    student_id = current_user.student.id

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
    student_id = current_user.student.id

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
    student_id = current_user.student.id

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
