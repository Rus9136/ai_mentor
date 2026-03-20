"""
Student-facing API endpoints for coding courses (learning paths).

Routes:
  GET  /coding/courses                        — courses with progress
  GET  /coding/courses/{slug}/lessons         — lessons in course
  GET  /coding/courses/lessons/{lesson_id}    — lesson detail
  POST /coding/courses/lessons/{lesson_id}/complete — mark lesson done
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_student_from_user,
)
from app.models.user import User
from app.models.student import Student
from app.services.coding_service import CourseService, CodingServiceError
from app.schemas.coding import (
    CourseWithProgress,
    LessonListItem,
    LessonDetail,
    LessonCompleteResponse,
)

router = APIRouter(prefix="/coding/courses")


async def get_course_service(db: AsyncSession = Depends(get_db)) -> CourseService:
    return CourseService(db)


# ---------------------------------------------------------------------------
# Courses
# ---------------------------------------------------------------------------

@router.get(
    "",
    response_model=list[CourseWithProgress],
    summary="List coding courses with progress",
)
async def list_courses(
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CourseService = Depends(get_course_service),
):
    return await service.list_courses_with_progress(student.id)


# ---------------------------------------------------------------------------
# Lessons
# ---------------------------------------------------------------------------

@router.get(
    "/{slug}/lessons",
    response_model=list[LessonListItem],
    summary="List lessons in a course",
)
async def list_lessons(
    slug: str,
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CourseService = Depends(get_course_service),
):
    try:
        return await service.list_lessons(slug, student.id)
    except CodingServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/lessons/{lesson_id}",
    response_model=LessonDetail,
    summary="Get lesson detail with theory and optional challenge",
)
async def get_lesson(
    lesson_id: int,
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CourseService = Depends(get_course_service),
):
    try:
        return await service.get_lesson_detail(lesson_id, student.id)
    except CodingServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post(
    "/lessons/{lesson_id}/complete",
    response_model=LessonCompleteResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark a lesson as completed",
)
async def complete_lesson(
    lesson_id: int,
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CourseService = Depends(get_course_service),
):
    try:
        return await service.complete_lesson(lesson_id, student.id, school_id=student.school_id)
    except CodingServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))
