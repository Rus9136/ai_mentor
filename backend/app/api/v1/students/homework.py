"""
Student Homework API endpoints.

Endpoints for students to:
- View assigned homework
- Start and complete tasks
- Submit answers to questions
- View results and feedback
"""

import logging
from typing import List, Optional
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.models.student import Student
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
    get_pagination_params,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services.homework import HomeworkService, HomeworkServiceError
from app.services.homework.ai import HomeworkAIService
from app.schemas.homework import (
    StudentHomeworkResponse,
    StudentTaskResponse,
    StudentQuestionResponse,
    StudentQuestionWithFeedback,
    AnswerSubmit,
    TaskSubmitRequest,
    SubmissionResult,
    TaskSubmissionResult,
    StudentHomeworkStatus,
    SubmissionStatus,
)

router = APIRouter()
logger = logging.getLogger(__name__)


# =============================================================================
# Service Dependencies
# =============================================================================

async def get_homework_service(
    db: AsyncSession = Depends(get_db)
) -> HomeworkService:
    """Get homework service with optional AI service."""
    ai_service = HomeworkAIService(db)
    return HomeworkService(db, ai_service)


# =============================================================================
# Homework List
# =============================================================================

@router.get(
    "/homework",
    response_model=PaginatedResponse[StudentHomeworkResponse],
    summary="Get my homework",
    description="Get list of homework assigned to the current student. Supports pagination."
)
async def list_my_homework(
    pagination: PaginationParams = Depends(get_pagination_params),
    hw_status: Optional[StudentHomeworkStatus] = Query(None, alias="status", description="Filter by status"),
    include_completed: bool = Query(True, description="Include completed homework"),
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> PaginatedResponse[StudentHomeworkResponse]:
    """
    Get homework assigned to student.

    Returns homework with due dates, progress, and scores.
    Supports pagination with `page` and `page_size` query parameters.
    """
    homework_list, total = await service.list_student_homework(
        student_id=student.id,
        school_id=school_id,
        status=hw_status,
        page=pagination.page,
        page_size=pagination.page_size,
    )

    now = datetime.now(timezone.utc)
    results = []

    for hw_student in homework_list:
        homework = hw_student.homework
        if not homework:
            continue

        # Skip completed if not requested
        if not include_completed and hw_student.status == StudentHomeworkStatus.GRADED:
            continue

        is_overdue = homework.due_date < now
        can_submit = True
        is_late = False

        if is_overdue:
            is_late = True
            if not homework.late_submission_allowed:
                can_submit = False
            elif homework.max_late_days:
                days_late = (now - homework.due_date).days
                if days_late > homework.max_late_days:
                    can_submit = False

        # Calculate max score
        max_score = sum(t.points for t in homework.tasks) if homework.tasks else 0

        # Build tasks response
        tasks_response = await _build_student_tasks(
            homework, hw_student, student.id, service
        )

        results.append(StudentHomeworkResponse(
            id=homework.id,
            title=homework.title,
            description=homework.description,
            due_date=homework.due_date,
            is_overdue=is_overdue,
            can_submit=can_submit,
            my_status=hw_student.status,
            my_score=hw_student.total_score,
            max_score=max_score,
            my_percentage=hw_student.percentage,
            is_late=is_late,
            late_penalty=0,  # Penalty calculated per-task in submissions
            show_explanations=homework.show_explanations,
            tasks=tasks_response
        ))

    return PaginatedResponse.create(results, total, pagination.page, pagination.page_size)


@router.get(
    "/homework/{homework_id}",
    response_model=StudentHomeworkResponse,
    summary="Get homework details",
    description="Get detailed homework with tasks and questions."
)
async def get_homework_detail(
    homework_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> StudentHomeworkResponse:
    """
    Get homework with full task and question details.
    """
    hw_student = await service.get_student_homework(
        homework_id=homework_id,
        student_id=student.id
    )

    if not hw_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found or not assigned to you"
        )

    homework = await service.get_homework(
        homework_id=homework_id,
        school_id=school_id,
        load_tasks=True,
        load_questions=True
    )

    if not homework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found"
        )

    now = datetime.now(timezone.utc)
    is_overdue = homework.due_date < now
    can_submit = True
    is_late = False

    if is_overdue:
        is_late = True
        if not homework.late_submission_allowed:
            can_submit = False
        elif homework.max_late_days:
            days_late = (now - homework.due_date).days
            if days_late > homework.max_late_days:
                can_submit = False

    max_score = sum(t.points for t in homework.tasks) if homework.tasks else 0

    tasks_response = await _build_student_tasks(
        homework, hw_student, student.id, service
    )

    return StudentHomeworkResponse(
        id=homework.id,
        title=homework.title,
        description=homework.description,
        due_date=homework.due_date,
        is_overdue=is_overdue,
        can_submit=can_submit,
        my_status=hw_student.status,
        my_score=hw_student.total_score,
        max_score=max_score,
        my_percentage=hw_student.percentage,
        is_late=is_late,
        late_penalty=0,  # Penalty calculated per-task in submissions
        show_explanations=homework.show_explanations,
        tasks=tasks_response
    )


# =============================================================================
# Task Operations
# =============================================================================

@router.post(
    "/homework/{homework_id}/tasks/{task_id}/start",
    response_model=StudentTaskResponse,
    summary="Start a task",
    description="Start a task attempt."
)
async def start_task(
    homework_id: int,
    task_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> StudentTaskResponse:
    """
    Start a task attempt.

    Creates a submission record and returns questions.
    """
    try:
        submission = await service.start_task(
            homework_id=homework_id,
            task_id=task_id,
            student_id=student.id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Get task with questions
    task = await service.get_task(task_id, school_id, load_questions=True)

    # Get attempts count
    attempts_used = await service.homework_repo.get_attempts_count(
        homework_student_id=submission.homework_student_id,
        task_id=task_id
    )

    return StudentTaskResponse(
        id=task.id,
        paragraph_id=task.paragraph_id,
        paragraph_title=None,
        task_type=task.task_type,
        instructions=task.instructions,
        points=task.points,
        time_limit_minutes=task.time_limit_minutes,
        status=SubmissionStatus.IN_PROGRESS,
        current_attempt=attempts_used,
        max_attempts=task.max_attempts,
        attempts_remaining=task.max_attempts - attempts_used,
        submission_id=submission.id,  # Include submission ID for answer submission
        questions_count=len(task.questions) if task.questions else 0,
        answered_count=0
    )


@router.get(
    "/homework/{homework_id}/tasks/{task_id}/questions",
    response_model=List[StudentQuestionResponse],
    summary="Get task questions",
    description="Get questions for a task (without correct answers)."
)
async def get_task_questions(
    homework_id: int,
    task_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> List[StudentQuestionResponse]:
    """
    Get questions for a task.

    Returns questions without correct answers.
    Includes student's previous answers if any.
    """
    # Verify assignment
    hw_student = await service.get_student_homework(homework_id, student.id)
    if not hw_student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found or not assigned to you"
        )

    task = await service.get_task(task_id, school_id, load_questions=True)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    # Get latest submission to check for existing answers
    submission = await service.homework_repo.get_latest_submission(
        homework_student_id=hw_student.id,
        task_id=task_id
    )

    answers_by_question = {}
    if submission:
        submission_with_answers = await service.homework_repo.get_submission_by_id(
            submission.id, load_answers=True
        )
        if submission_with_answers and submission_with_answers.answers:
            for ans in submission_with_answers.answers:
                answers_by_question[ans.question_id] = ans

    results = []
    for q in (task.questions or []):
        # Remove correct answer info from options
        clean_options = None
        if q.options:
            clean_options = [
                {"id": opt.get("id"), "text": opt.get("text")}
                for opt in q.options
            ]

        my_answer = None
        my_selected = None
        is_answered = False

        if q.id in answers_by_question:
            ans = answers_by_question[q.id]
            my_answer = ans.answer_text
            my_selected = ans.selected_option_ids
            is_answered = True

        results.append(StudentQuestionResponse(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=clean_options,
            points=q.points,
            my_answer=my_answer,
            my_selected_options=my_selected,
            is_answered=is_answered
        ))

    return results


# =============================================================================
# Submissions
# =============================================================================

@router.post(
    "/homework/submissions/{submission_id}/answer",
    response_model=SubmissionResult,
    summary="Submit an answer",
    description="Submit an answer for a single question."
)
async def submit_answer(
    submission_id: int,
    data: AnswerSubmit,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> SubmissionResult:
    """
    Submit an answer for a question.

    For choice questions, returns immediate feedback.
    For open-ended, may return AI feedback or flag for teacher review.
    """
    try:
        result = await service.submit_answer(
            submission_id=submission_id,
            question_id=data.question_id,
            answer_text=data.answer_text,
            selected_options=data.selected_options,
            student_id=student.id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return result


@router.post(
    "/homework/submissions/{submission_id}/complete",
    response_model=TaskSubmissionResult,
    summary="Complete submission",
    description="Complete a task submission and get final score."
)
async def complete_submission(
    submission_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> TaskSubmissionResult:
    """
    Complete a task submission.

    Calculates final score with any late penalties applied.
    """
    try:
        result = await service.complete_submission(
            submission_id=submission_id,
            student_id=student.id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return result


@router.get(
    "/homework/submissions/{submission_id}/results",
    response_model=List[StudentQuestionWithFeedback],
    summary="Get submission results",
    description="Get results with feedback for completed submission."
)
async def get_submission_results(
    submission_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> List[StudentQuestionWithFeedback]:
    """
    Get results for a completed submission.

    Returns answers with correct/incorrect status and explanations
    if homework settings allow.
    """
    submission = await service.homework_repo.get_submission_by_id(
        submission_id, load_answers=True
    )

    if not submission:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Submission not found"
        )

    if submission.student_id != student.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to view this submission"
        )

    # Get homework to check show_explanations setting
    hw_student = await service.homework_repo.get_student_homework(
        homework_id=submission.homework_student.homework_id,
        student_id=student.id
    )
    homework = hw_student.homework if hw_student else None
    show_explanations = homework.show_explanations if homework else False

    results = []
    for answer in (submission.answers or []):
        question = await service.homework_repo.get_question_by_id(answer.question_id)
        if not question:
            continue

        # Clean options for student view
        clean_options = None
        if question.options:
            clean_options = [
                {
                    "id": opt.get("id"),
                    "text": opt.get("text"),
                    "is_correct": opt.get("is_correct") if show_explanations else None
                }
                for opt in question.options
            ]

        results.append(StudentQuestionWithFeedback(
            id=question.id,
            question_text=question.question_text,
            question_type=question.question_type,
            options=clean_options,
            points=question.points,
            my_answer=answer.answer_text,
            my_selected_options=answer.selected_option_ids,
            is_answered=True,
            is_correct=answer.is_correct,
            score=answer.partial_score,
            max_score=question.points,
            explanation=question.explanation if show_explanations else None,
            ai_feedback=answer.ai_feedback,
            ai_confidence=answer.ai_confidence
        ))

    return results


# =============================================================================
# Helper Functions
# =============================================================================

async def _build_student_tasks(
    homework, hw_student, student_id: int, service: HomeworkService
) -> List[StudentTaskResponse]:
    """
    Build task responses for student view.

    Uses batch queries to avoid N+1 problem:
    - 1 query for all attempt counts
    - 1 query for all latest submissions
    Instead of 2N queries (2 per task).
    """
    tasks = homework.tasks or []
    if not tasks:
        return []

    task_ids = [task.id for task in tasks]

    # Batch fetch: 2 queries instead of 2N
    attempts_map = await service.homework_repo.get_attempts_counts_batch(
        homework_student_id=hw_student.id,
        task_ids=task_ids
    )
    submissions_map = await service.homework_repo.get_latest_submissions_batch(
        homework_student_id=hw_student.id,
        task_ids=task_ids
    )

    tasks_response = []
    for task in tasks:
        attempts_used = attempts_map.get(task.id, 0)
        latest_submission = submissions_map.get(task.id)

        status = SubmissionStatus.NOT_STARTED
        my_score = None
        answered_count = 0

        if latest_submission:
            status = SubmissionStatus(latest_submission.status.value)
            my_score = latest_submission.score
            if latest_submission.answers:
                answered_count = len(latest_submission.answers)

        tasks_response.append(StudentTaskResponse(
            id=task.id,
            paragraph_id=task.paragraph_id,
            paragraph_title=None,
            task_type=task.task_type,
            instructions=task.instructions,
            points=task.points,
            time_limit_minutes=task.time_limit_minutes,
            status=status,
            current_attempt=attempts_used,
            max_attempts=task.max_attempts,
            attempts_remaining=max(0, task.max_attempts - attempts_used),
            submission_id=latest_submission.id if latest_submission else None,
            my_score=my_score,
            questions_count=len(task.questions) if task.questions else 0,
            answered_count=answered_count
        ))

    return tasks_response
