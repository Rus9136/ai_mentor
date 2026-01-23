"""
Teacher Homework API endpoints.

Endpoints for teachers to:
- Create and manage homework assignments
- Add tasks and questions (manual or AI-generated)
- Publish homework to students
- Review student answers
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile, status

from app.api.dependencies import (
    get_current_user_school_id,
    get_homework_service,
    get_teacher_from_user,
    verify_homework_ownership,
    verify_task_ownership,
)
from app.models.homework import Homework, HomeworkTask
from app.models.teacher import Teacher
from app.schemas.homework import (
    AnswerForReview,
    GenerationParams,
    HomeworkCreate,
    HomeworkListResponse,
    HomeworkResponse,
    HomeworkStatus,
    HomeworkTaskCreate,
    HomeworkTaskResponse,
    HomeworkUpdate,
    QuestionCreate,
    QuestionResponseWithAnswer,
    TeacherReviewRequest,
    TeacherReviewResponse,
)
from app.services.homework import HomeworkService, HomeworkServiceError
from app.services.homework.ai import HomeworkAIServiceError
from app.services.homework.response_builder import HomeworkResponseBuilder
from app.services.upload_service import UploadService
from app.schemas.upload import FileUploadResponse

router = APIRouter(prefix="/teachers/homework", tags=["teachers-homework"])

# Upload service instance
upload_service = UploadService(upload_dir="uploads")


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
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """Create a new homework assignment in DRAFT status."""
    homework = await service.create_homework(
        data=data,
        school_id=school_id,
        teacher_id=teacher.id
    )

    # Get with tasks for response
    homework = await service.get_homework(homework.id, school_id, load_tasks=True)
    return HomeworkResponseBuilder.build_homework_response(homework)


@router.get(
    "",
    response_model=List[HomeworkListResponse],
    summary="List teacher's homework",
    description="Get list of homework assignments created by the current teacher."
)
async def list_homework(
    class_id: Optional[int] = Query(None, description="Filter by class"),
    homework_status: Optional[HomeworkStatus] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Pagination offset"),
    limit: int = Query(20, ge=1, le=100, description="Pagination limit"),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> List[HomeworkListResponse]:
    """List homework created by teacher with optional filters."""
    homework_list = await service.list_homework_by_teacher(
        teacher_id=teacher.id,
        school_id=school_id,
        status=homework_status,
        class_id=class_id,
        skip=skip,
        limit=limit
    )

    # Get statistics for all homework in one batch query
    homework_ids = [hw.id for hw in homework_list]
    stats_map = await service.get_homework_stats_batch(homework_ids) if homework_ids else {}

    return [
        HomeworkListResponse(
            id=hw.id,
            title=hw.title,
            status=hw.status,
            due_date=hw.due_date,
            class_id=hw.class_id,
            class_name=hw.school_class.name if hw.school_class else None,
            tasks_count=len(hw.tasks) if hw.tasks else 0,
            total_students=stats_map.get(hw.id, {}).get("total_students", 0),
            submitted_count=stats_map.get(hw.id, {}).get("submitted_count", 0),
            ai_generation_enabled=hw.ai_generation_enabled,
            created_at=hw.created_at
        )
        for hw in homework_list
    ]


# =============================================================================
# Teacher Review (must be BEFORE /{homework_id} to avoid route conflicts)
# =============================================================================

@router.get(
    "/review-queue",
    response_model=List[AnswerForReview],
    summary="Get answers for review",
    description="Get student answers flagged for teacher review."
)
async def get_review_queue(
    homework_id: Optional[int] = Query(default=None, description="Filter by homework"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> List[AnswerForReview]:
    """Get answers needing teacher review (open-ended with low AI confidence)."""
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
            student_name=f"{a.student.user.first_name} {a.student.user.last_name}" if a.student and a.student.user else "",
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
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> TeacherReviewResponse:
    """Review and grade a student answer. Teacher can override AI score."""
    answer = await service.review_answer(
        answer_id=answer_id,
        teacher_id=teacher.id,
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
# File Upload
# =============================================================================

@router.post(
    "/upload",
    response_model=FileUploadResponse,
    summary="Upload file for homework",
    description="Upload a file (image, PDF, doc) to attach to homework or task."
)
async def upload_homework_file(
    file: UploadFile = File(...),
    teacher: Teacher = Depends(get_teacher_from_user),
) -> FileUploadResponse:
    """
    Upload a file for homework attachment.

    Supported types:
    - Images: JPEG, PNG, WebP, GIF (max 5 MB)
    - PDF: (max 50 MB)
    - Documents: DOC, DOCX, XLS, XLSX, PPT, PPTX, TXT (max 20 MB)
    """
    try:
        result = await upload_service.save_homework_file(file)
        return FileUploadResponse(**result)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Ошибка загрузки файла: {str(e)}"
        ) from e


# =============================================================================
# Homework Detail (with path parameter - must be AFTER literal paths)
# =============================================================================

@router.get(
    "/{homework_id}",
    response_model=HomeworkResponse,
    summary="Get homework details",
    description="Get detailed homework information including tasks and questions."
)
async def get_homework(
    homework: Homework = Depends(verify_homework_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """Get homework with tasks, questions and statistics."""
    # Get statistics for the homework
    stats = await service.get_homework_stats(homework.id, school_id)
    return HomeworkResponseBuilder.build_homework_response(homework, stats=stats)


@router.put(
    "/{homework_id}",
    response_model=HomeworkResponse,
    summary="Update homework",
    description="Update homework (only in draft status)."
)
async def update_homework(
    data: HomeworkUpdate,
    homework: Homework = Depends(verify_homework_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """Update homework details. Only works for DRAFT status."""
    try:
        updated = await service.update_homework(
            homework_id=homework.id,
            data=data,
            school_id=school_id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    return HomeworkResponseBuilder.build_homework_response(updated)


@router.delete(
    "/{homework_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete homework",
    description="Delete homework draft. Only works for DRAFT status."
)
async def delete_homework(
    homework: Homework = Depends(verify_homework_ownership),
    school_id: int = Depends(get_current_user_school_id),
    teacher: Teacher = Depends(get_teacher_from_user),
    service: HomeworkService = Depends(get_homework_service)
) -> None:
    """Delete homework draft. Only works for DRAFT status."""
    try:
        deleted = await service.delete_homework(
            homework_id=homework.id,
            school_id=school_id,
            teacher_id=teacher.id
        )
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Homework not found"
            )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


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
    student_ids: Optional[List[int]] = None,
    homework: Homework = Depends(verify_homework_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """Publish homework to students. If student_ids not provided, assigns to all in class."""
    try:
        published = await service.publish_homework(
            homework_id=homework.id,
            school_id=school_id,
            student_ids=student_ids
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    # Get statistics after publishing
    stats = await service.get_homework_stats(published.id, school_id)
    return HomeworkResponseBuilder.build_homework_response(published, stats=stats)


@router.post(
    "/{homework_id}/close",
    response_model=HomeworkResponse,
    summary="Close homework",
    description="Close homework for submissions."
)
async def close_homework(
    homework: Homework = Depends(verify_homework_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkResponse:
    """Close homework for new submissions."""
    try:
        closed = await service.close_homework(
            homework_id=homework.id,
            school_id=school_id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    # Get final statistics
    stats = await service.get_homework_stats(closed.id, school_id)
    return HomeworkResponseBuilder.build_homework_response(closed, stats=stats)


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
    data: HomeworkTaskCreate,
    homework: Homework = Depends(verify_homework_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> HomeworkTaskResponse:
    """Add a task to homework. Tasks can be linked to paragraphs or chapters."""
    try:
        task = await service.add_task(
            homework_id=homework.id,
            data=data,
            school_id=school_id
        )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    return HomeworkResponseBuilder.build_task_response(task, include_questions=False)


@router.delete(
    "/tasks/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete task",
    description="Remove a task from homework (only draft)."
)
async def delete_task(
    task: HomeworkTask = Depends(verify_task_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> None:
    """Delete a task from homework. Only works for DRAFT status."""
    try:
        deleted = await service.delete_task(task.id, school_id)
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Задание не найдено или уже удалено"
            )
    except HomeworkServiceError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e


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
    data: QuestionCreate,
    task: HomeworkTask = Depends(verify_task_ownership),
    service: HomeworkService = Depends(get_homework_service)
) -> QuestionResponseWithAnswer:
    """Add a question to a task. Supports all question types."""
    question = await service.add_question(task.id, task.school_id, data)
    return HomeworkResponseBuilder.build_question_with_answer(question)


@router.post(
    "/tasks/{task_id}/generate-questions",
    response_model=List[QuestionResponseWithAnswer],
    summary="Generate questions with AI",
    description="Use AI to generate questions based on paragraph content."
)
async def generate_questions(
    params: Optional[GenerationParams] = None,
    regenerate: bool = Query(False, description="Replace existing questions"),
    task: HomeworkTask = Depends(verify_task_ownership),
    school_id: int = Depends(get_current_user_school_id),
    service: HomeworkService = Depends(get_homework_service)
) -> List[QuestionResponseWithAnswer]:
    """Generate questions using AI based on the paragraph content."""
    # Use default params if not provided
    generation_params = params or GenerationParams()

    # Update task with generation params (for persistence)
    await service.homework_repo.update_task(
        task_id=task.id,
        school_id=school_id,
        data={"generation_params": generation_params.model_dump()}
    )

    try:
        # Pass params directly to avoid transaction/identity issues
        questions = await service.generate_questions_for_task(
            task_id=task.id,
            school_id=school_id,
            regenerate=regenerate,
            params=generation_params
        )
    except (HomeworkServiceError, HomeworkAIServiceError) as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        ) from e

    return [
        HomeworkResponseBuilder.build_question_with_answer(q)
        for q in questions
    ]
