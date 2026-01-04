"""
Teacher Homework API endpoints.

Endpoints for teachers to:
- Create and manage homework assignments
- Add tasks and questions (manual or AI-generated)
- Publish homework to students
- Review student answers
"""

from typing import List, Optional
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import (
    require_teacher,
    get_current_user_school_id,
)
from app.services.homework_service import HomeworkService, HomeworkServiceError
from app.services.homework_ai_service import HomeworkAIService
from app.schemas.homework import (
    HomeworkCreate,
    HomeworkUpdate,
    HomeworkResponse,
    HomeworkListResponse,
    HomeworkTaskCreate,
    HomeworkTaskResponse,
    QuestionCreate,
    QuestionResponse,
    QuestionResponseWithAnswer,
    GenerationParams,
    AnswerForReview,
    TeacherReviewRequest,
    TeacherReviewResponse,
    HomeworkStatus,
)

router = APIRouter(prefix="/teachers/homework", tags=["teachers-homework"])


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
# Homework CRUD
# =============================================================================

@router.post(
    "",
    response_model=HomeworkResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create homework assignment",
    description="Create a new homework assignment in draft status."
)
async def create_homework(
    data: HomeworkCreate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """
    Create a new homework assignment.

    The homework is created in DRAFT status. Add tasks and questions,
    then publish to assign to students.
    """
    homework = await service.create_homework(
        data=data,
        school_id=school_id,
        teacher_id=current_user.id
    )

    # Get with tasks for response
    homework = await service.get_homework(homework.id, school_id, load_tasks=True)

    return _homework_to_response(homework)


@router.get(
    "",
    response_model=List[HomeworkListResponse],
    summary="List teacher's homework",
    description="Get list of homework assignments created by the current teacher."
)
async def list_homework(
    class_id: Optional[int] = Query(None, description="Filter by class"),
    status: Optional[HomeworkStatus] = Query(None, description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> List[HomeworkListResponse]:
    """
    List homework created by teacher.

    Supports filtering by class and status.
    """
    homework_list = await service.list_homework_by_teacher(
        teacher_id=current_user.id,
        school_id=school_id,
        status=status,
        class_id=class_id,
        skip=skip,
        limit=limit
    )

    return [
        HomeworkListResponse(
            id=hw.id,
            title=hw.title,
            status=hw.status,
            due_date=hw.due_date,
            class_id=hw.class_id,
            class_name=None,  # Would need join
            tasks_count=len(hw.tasks) if hw.tasks else 0,
            ai_generation_enabled=hw.ai_generation_enabled,
            created_at=hw.created_at
        )
        for hw in homework_list
    ]


@router.get(
    "/{homework_id}",
    response_model=HomeworkResponse,
    summary="Get homework details",
    description="Get detailed homework information including tasks and questions."
)
async def get_homework(
    homework_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """
    Get homework with tasks and questions.
    """
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

    # Verify ownership
    if homework.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only view your own homework"
        )

    return _homework_to_response(homework)


@router.put(
    "/{homework_id}",
    response_model=HomeworkResponse,
    summary="Update homework",
    description="Update homework (only in draft status)."
)
async def update_homework(
    homework_id: int,
    data: HomeworkUpdate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """
    Update homework details.

    Only works for homework in DRAFT status.
    """
    # Verify ownership first
    existing = await service.get_homework(homework_id, school_id, load_tasks=False)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found"
        )
    if existing.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only update your own homework"
        )

    try:
        homework = await service.update_homework(
            homework_id=homework_id,
            data=data,
            school_id=school_id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _homework_to_response(homework)


# =============================================================================
# Publishing
# =============================================================================

@router.post(
    "/{homework_id}/publish",
    response_model=HomeworkResponse,
    summary="Publish homework",
    description="Publish homework and assign to students in the class."
)
async def publish_homework(
    homework_id: int,
    student_ids: Optional[List[int]] = None,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """
    Publish homework to students.

    If student_ids is not provided, assigns to all students in the class.
    """
    # Verify ownership
    existing = await service.get_homework(homework_id, school_id, load_tasks=True)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found"
        )
    if existing.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only publish your own homework"
        )

    try:
        homework = await service.publish_homework(
            homework_id=homework_id,
            school_id=school_id,
            student_ids=student_ids
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _homework_to_response(homework)


@router.post(
    "/{homework_id}/close",
    response_model=HomeworkResponse,
    summary="Close homework",
    description="Close homework for submissions."
)
async def close_homework(
    homework_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """
    Close homework for new submissions.
    """
    existing = await service.get_homework(homework_id, school_id, load_tasks=False)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found"
        )
    if existing.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only close your own homework"
        )

    try:
        homework = await service.close_homework(
            homework_id=homework_id,
            school_id=school_id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return _homework_to_response(homework)


# =============================================================================
# Tasks
# =============================================================================

@router.post(
    "/{homework_id}/tasks",
    response_model=HomeworkTaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add task to homework",
    description="Add a task (linked to paragraph/chapter) to homework."
)
async def add_task(
    homework_id: int,
    data: HomeworkTaskCreate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkTaskResponse:
    """
    Add a task to homework.

    Tasks can be linked to paragraphs or chapters.
    Questions can be added manually or generated via AI.
    """
    # Verify ownership
    existing = await service.get_homework(homework_id, school_id, load_tasks=False)
    if not existing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Homework not found"
        )
    if existing.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own homework"
        )

    try:
        task = await service.add_task(
            homework_id=homework_id,
            data=data,
            school_id=school_id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return HomeworkTaskResponse(
        id=task.id,
        paragraph_id=task.paragraph_id,
        chapter_id=task.chapter_id,
        task_type=task.task_type,
        sort_order=task.sort_order,
        is_required=task.is_required,
        points=task.points,
        time_limit_minutes=task.time_limit_minutes,
        max_attempts=task.max_attempts,
        ai_generated=task.ai_generated,
        instructions=task.instructions,
        questions_count=0,
        questions=[]
    )


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Remove a task from homework (only draft)."
)
async def delete_task(
    task_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> None:
    """
    Delete a task from homework.

    Only works for homework in DRAFT status.
    """
    try:
        deleted = await service.delete_task(task_id, school_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found"
            )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# =============================================================================
# Questions
# =============================================================================

@router.post(
    "/tasks/{task_id}/questions",
    response_model=QuestionResponseWithAnswer,
    status_code=status.HTTP_201_CREATED,
    summary="Add question to task",
    description="Manually add a question to a task."
)
async def add_question(
    task_id: int,
    data: QuestionCreate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> QuestionResponseWithAnswer:
    """
    Add a question to a task.

    Supports all question types: single_choice, multiple_choice,
    true_false, short_answer, open_ended.
    """
    # Verify task exists and belongs to teacher's homework
    task = await service.get_task(task_id, school_id, load_questions=False)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    homework = await service.get_homework(task.homework_id, school_id, load_tasks=False)
    if not homework or homework.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own homework"
        )

    question = await service.add_question(task_id, data)

    return QuestionResponseWithAnswer(
        id=question.id,
        question_text=question.question_text,
        question_type=question.question_type,
        options=question.options,
        points=question.points,
        difficulty=question.difficulty,
        bloom_level=question.bloom_level,
        explanation=question.explanation,
        version=question.version,
        is_active=question.is_active,
        ai_generated=question.ai_generated,
        created_at=question.created_at,
        correct_answer=question.correct_answer,
        grading_rubric=question.grading_rubric,
        expected_answer_hints=question.expected_answer_hints
    )


@router.post(
    "/tasks/{task_id}/generate-questions",
    response_model=List[QuestionResponseWithAnswer],
    summary="Generate questions with AI",
    description="Use AI to generate questions based on paragraph content."
)
async def generate_questions(
    task_id: int,
    params: Optional[GenerationParams] = None,
    regenerate: bool = Query(False, description="Replace existing questions"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> List[QuestionResponseWithAnswer]:
    """
    Generate questions using AI.

    Uses the paragraph content linked to the task.
    Customize generation with params (question types, Bloom levels, count).
    """
    # Verify task exists and belongs to teacher's homework
    task = await service.get_task(task_id, school_id, load_questions=False)
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )

    homework = await service.get_homework(task.homework_id, school_id, load_tasks=False)
    if not homework or homework.teacher_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only modify your own homework"
        )

    # Update task with generation params if provided
    if params:
        await service.homework_repo.update_task(
            task_id=task_id,
            school_id=school_id,
            data={"generation_params": params.model_dump()}
        )

    try:
        questions = await service.generate_questions_for_task(
            task_id=task_id,
            school_id=school_id,
            regenerate=regenerate
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    return [
        QuestionResponseWithAnswer(
            id=q.id,
            question_text=q.question_text,
            question_type=q.question_type,
            options=q.options,
            points=q.points,
            difficulty=q.difficulty,
            bloom_level=q.bloom_level,
            explanation=q.explanation,
            version=q.version,
            is_active=q.is_active,
            ai_generated=q.ai_generated,
            created_at=q.created_at,
            correct_answer=q.correct_answer,
            grading_rubric=q.grading_rubric,
            expected_answer_hints=q.expected_answer_hints
        )
        for q in questions
    ]


# =============================================================================
# Teacher Review
# =============================================================================

@router.get(
    "/review-queue",
    response_model=List[AnswerForReview],
    summary="Get answers for review",
    description="Get student answers flagged for teacher review."
)
async def get_review_queue(
    homework_id: Optional[int] = Query(None, description="Filter by homework"),
    limit: int = Query(50, ge=1, le=200, description="Max results"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> List[AnswerForReview]:
    """
    Get answers needing teacher review.

    Returns open-ended answers with low AI confidence
    that require manual grading.
    """
    answers = await service.get_answers_for_review(
        school_id=school_id,
        homework_id=homework_id,
        limit=limit
    )

    return [
        AnswerForReview(
            id=a.id,
            question_id=a.question_id,
            question_text=a.question.question_text if a.question else "",
            question_type=a.question.question_type if a.question else "open_ended",
            student_id=a.student_id,
            student_name=f"{a.student.first_name} {a.student.last_name}" if a.student else "",
            answer_text=a.answer_text,
            submitted_at=a.answered_at,
            ai_score=a.ai_score,
            ai_confidence=a.ai_confidence,
            ai_feedback=a.ai_feedback,
            grading_rubric=a.question.grading_rubric if a.question else None,
            expected_answer_hints=a.question.expected_answer_hints if a.question else None
        )
        for a in answers
    ]


@router.post(
    "/answers/{answer_id}/review",
    response_model=TeacherReviewResponse,
    summary="Review student answer",
    description="Teacher reviews and grades a student answer."
)
async def review_answer(
    answer_id: int,
    data: TeacherReviewRequest,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> TeacherReviewResponse:
    """
    Review and grade a student answer.

    Teacher can override AI score and provide feedback.
    """
    answer = await service.review_answer(
        answer_id=answer_id,
        teacher_id=current_user.id,
        score=data.score / 100.0,  # Convert to 0-1 scale
        feedback=data.feedback
    )

    if not answer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Answer not found"
        )

    return TeacherReviewResponse(
        answer_id=answer.id,
        teacher_score=answer.teacher_override_score * 100 if answer.teacher_override_score else 0,
        teacher_feedback=answer.teacher_comment,
        reviewed_at=answer.updated_at
    )


# =============================================================================
# Helper Functions
# =============================================================================

def _homework_to_response(homework) -> HomeworkResponse:
    """Convert Homework model to response schema."""
    tasks_response = []
    if homework.tasks:
        for task in homework.tasks:
            questions_response = []
            if hasattr(task, 'questions') and task.questions:
                for q in task.questions:
                    questions_response.append(QuestionResponse(
                        id=q.id,
                        question_text=q.question_text,
                        question_type=q.question_type,
                        options=q.options,
                        points=q.points,
                        difficulty=q.difficulty,
                        bloom_level=q.bloom_level,
                        explanation=q.explanation,
                        version=q.version,
                        is_active=q.is_active,
                        ai_generated=q.ai_generated,
                        created_at=q.created_at
                    ))

            tasks_response.append(HomeworkTaskResponse(
                id=task.id,
                paragraph_id=task.paragraph_id,
                chapter_id=task.chapter_id,
                task_type=task.task_type,
                sort_order=task.sort_order,
                is_required=task.is_required,
                points=task.points,
                time_limit_minutes=task.time_limit_minutes,
                max_attempts=task.max_attempts,
                ai_generated=task.ai_generated,
                instructions=task.instructions,
                questions_count=len(questions_response),
                questions=questions_response
            ))

    return HomeworkResponse(
        id=homework.id,
        title=homework.title,
        description=homework.description,
        status=homework.status,
        due_date=homework.due_date,
        class_id=homework.class_id,
        teacher_id=homework.teacher_id,
        ai_generation_enabled=homework.ai_generation_enabled,
        ai_check_enabled=homework.ai_check_enabled,
        target_difficulty=homework.target_difficulty,
        personalization_enabled=homework.personalization_enabled,
        auto_check_enabled=homework.auto_check_enabled,
        show_answers_after=homework.show_answers_after,
        show_explanations=homework.show_explanations,
        late_submission_allowed=homework.late_submission_allowed,
        late_penalty_per_day=homework.late_penalty_per_day,
        grace_period_hours=homework.grace_period_hours,
        max_late_days=homework.max_late_days,
        tasks=tasks_response,
        created_at=homework.created_at,
        updated_at=homework.updated_at
    )
