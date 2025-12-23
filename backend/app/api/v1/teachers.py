"""
Teacher Dashboard API endpoints.

Итерация 11: API для Teacher Dashboard.
- Dashboard overview
- Classes list and detail
- Student progress tracking
- Analytics (struggling topics, trends)
- Assignment management (MVP+)

All endpoints require TEACHER role.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import (
    require_teacher,
    get_current_user_school_id,
)
from app.services.teacher_analytics_service import TeacherAnalyticsService
from app.schemas.teacher_dashboard import (
    TeacherDashboardResponse,
    TeacherClassResponse,
    TeacherClassDetailResponse,
    ClassOverviewResponse,
    MasteryDistributionResponse,
    StudentProgressDetailResponse,
    MasteryHistoryResponse,
    StrugglingTopicResponse,
    MasteryTrendsResponse,
    AssignmentCreate,
    AssignmentUpdate,
    AssignmentResponse,
    AssignmentDetailResponse,
)

router = APIRouter(prefix="/teachers", tags=["teachers"])


# ============================================================================
# DASHBOARD
# ============================================================================

@router.get(
    "/dashboard",
    response_model=TeacherDashboardResponse,
    summary="Get teacher dashboard",
    description="Get overview statistics for teacher dashboard: classes count, students, mastery distribution."
)
async def get_dashboard(
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> TeacherDashboardResponse:
    """
    Get teacher dashboard data.

    Returns:
    - classes_count: Number of classes the teacher is assigned to
    - total_students: Total number of students across all classes
    - students_by_level: Distribution of students by mastery level (A/B/C)
    - average_class_score: Average mastery score across all classes
    - students_needing_help: Number of students in level C
    """
    service = TeacherAnalyticsService(db)
    return await service.get_dashboard(current_user.id, school_id)


# ============================================================================
# CLASSES
# ============================================================================

@router.get(
    "/classes",
    response_model=List[TeacherClassResponse],
    summary="Get teacher's classes",
    description="Get list of all classes assigned to the current teacher."
)
async def get_classes(
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> List[TeacherClassResponse]:
    """
    Get list of classes for the current teacher.

    Returns list of classes with:
    - Basic info (name, code, grade level)
    - Students count
    - Mastery distribution (A/B/C)
    - Average score and progress
    """
    service = TeacherAnalyticsService(db)
    return await service.get_classes(current_user.id, school_id)


@router.get(
    "/classes/{class_id}",
    response_model=TeacherClassDetailResponse,
    summary="Get class detail",
    description="Get detailed information about a specific class including all students."
)
async def get_class_detail(
    class_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> TeacherClassDetailResponse:
    """
    Get detailed class information.

    Returns:
    - Class info
    - List of all students with their mastery levels
    - Mastery distribution
    - Average scores
    """
    service = TeacherAnalyticsService(db)
    result = await service.get_class_detail(current_user.id, school_id, class_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you don't have access to it"
        )

    return result


@router.get(
    "/classes/{class_id}/overview",
    response_model=ClassOverviewResponse,
    summary="Get class overview",
    description="Get class overview with chapter-by-chapter analytics."
)
async def get_class_overview(
    class_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> ClassOverviewResponse:
    """
    Get class overview with analytics.

    Returns:
    - Class info with mastery distribution
    - Per-chapter progress breakdown
    - Trend analysis (improving/stable/declining)
    """
    service = TeacherAnalyticsService(db)
    result = await service.get_class_overview(current_user.id, school_id, class_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you don't have access to it"
        )

    return result


@router.get(
    "/classes/{class_id}/mastery-distribution",
    response_model=MasteryDistributionResponse,
    summary="Get mastery distribution",
    description="Get detailed A/B/C distribution for a class with student breakdown."
)
async def get_mastery_distribution(
    class_id: int,
    chapter_id: Optional[int] = Query(None, description="Optional chapter filter"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> MasteryDistributionResponse:
    """
    Get detailed mastery distribution.

    Optionally filter by chapter_id.

    Returns:
    - Distribution counts (A/B/C)
    - Lists of students in each level
    """
    service = TeacherAnalyticsService(db)

    # Get class detail for distribution
    result = await service.get_class_detail(current_user.id, school_id, class_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you don't have access to it"
        )

    # Build distribution response
    from app.schemas.teacher_dashboard import StudentBriefResponse, MasteryDistribution

    students_a = []
    students_b = []
    students_c = []

    for student in result.students:
        brief = StudentBriefResponse(
            id=student.id,
            student_code=student.student_code,
            grade_level=0,  # Not available in StudentWithMastery
            first_name=student.first_name,
            last_name=student.last_name,
            middle_name=student.middle_name
        )

        if student.mastery_level == "A":
            students_a.append(brief)
        elif student.mastery_level == "B":
            students_b.append(brief)
        elif student.mastery_level == "C":
            students_c.append(brief)

    return MasteryDistributionResponse(
        class_id=class_id,
        class_name=result.name,
        chapter_id=chapter_id,
        chapter_name=None,  # TODO: get chapter name if filter applied
        distribution=result.mastery_distribution,
        students_level_a=students_a,
        students_level_b=students_b,
        students_level_c=students_c
    )


# ============================================================================
# STUDENT PROGRESS
# ============================================================================

@router.get(
    "/classes/{class_id}/students/{student_id}/progress",
    response_model=StudentProgressDetailResponse,
    summary="Get student progress",
    description="Get detailed progress for a specific student."
)
async def get_student_progress(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> StudentProgressDetailResponse:
    """
    Get detailed student progress.

    Returns:
    - Student info
    - Overall mastery level and score
    - Per-chapter progress
    - Recent test attempts
    - Activity info
    """
    service = TeacherAnalyticsService(db)
    result = await service.get_student_progress(
        current_user.id, school_id, class_id, student_id
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found or you don't have access to this class"
        )

    return result


@router.get(
    "/students/{student_id}/mastery-history",
    response_model=MasteryHistoryResponse,
    summary="Get student mastery history",
    description="Get timeline of mastery level changes for a student."
)
async def get_student_mastery_history(
    student_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> MasteryHistoryResponse:
    """
    Get mastery history timeline.

    Returns list of mastery level changes with:
    - Previous and new levels
    - Score changes
    - When the change occurred
    """
    service = TeacherAnalyticsService(db)
    result = await service.get_mastery_history(current_user.id, school_id, student_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )

    return result


# ============================================================================
# ANALYTICS
# ============================================================================

@router.get(
    "/analytics/struggling-topics",
    response_model=List[StrugglingTopicResponse],
    summary="Get struggling topics",
    description="Get topics where students are struggling (>30% in level C)."
)
async def get_struggling_topics(
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> List[StrugglingTopicResponse]:
    """
    Get topics where many students are struggling.

    Returns list of paragraphs ordered by struggling count:
    - Paragraph and chapter info
    - Number of struggling students
    - Percentage of students struggling
    - Average score
    """
    service = TeacherAnalyticsService(db)
    return await service.get_struggling_topics(current_user.id, school_id)


@router.get(
    "/analytics/mastery-trends",
    response_model=MasteryTrendsResponse,
    summary="Get mastery trends",
    description="Get mastery trends over time (weekly or monthly)."
)
async def get_mastery_trends(
    period: str = Query("weekly", regex="^(weekly|monthly)$"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> MasteryTrendsResponse:
    """
    Get mastery trends across classes.

    Args:
        period: "weekly" or "monthly"

    Returns:
    - Overall trend (improving/stable/declining)
    - Per-class trends with change percentages
    """
    service = TeacherAnalyticsService(db)
    return await service.get_mastery_trends(current_user.id, school_id, period)


# ============================================================================
# ASSIGNMENTS (MVP+)
# ============================================================================

@router.get(
    "/assignments",
    response_model=List[AssignmentResponse],
    summary="Get assignments",
    description="Get list of assignments created by the teacher."
)
async def get_assignments(
    class_id: Optional[int] = Query(None, description="Filter by class"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> List[AssignmentResponse]:
    """
    Get list of assignments.

    Optionally filter by class_id.

    Returns list of assignments with completion stats.
    """
    # TODO: Implement assignment listing
    # For MVP, return empty list
    return []


@router.post(
    "/assignments",
    response_model=AssignmentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create assignment",
    description="Create a new assignment for a class."
)
async def create_assignment(
    assignment: AssignmentCreate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> AssignmentResponse:
    """
    Create a new assignment.

    Assigns content (chapter, paragraph, or test) to a class with optional deadline.
    """
    # TODO: Implement assignment creation
    raise HTTPException(
        status_code=status.HTTP_501_NOT_IMPLEMENTED,
        detail="Assignment creation not yet implemented"
    )


@router.get(
    "/assignments/{assignment_id}",
    response_model=AssignmentDetailResponse,
    summary="Get assignment detail",
    description="Get detailed assignment info with student progress."
)
async def get_assignment_detail(
    assignment_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> AssignmentDetailResponse:
    """
    Get detailed assignment info.

    Returns assignment with all students' progress.
    """
    # TODO: Implement assignment detail
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Assignment not found"
    )


@router.put(
    "/assignments/{assignment_id}",
    response_model=AssignmentResponse,
    summary="Update assignment",
    description="Update an existing assignment."
)
async def update_assignment(
    assignment_id: int,
    assignment: AssignmentUpdate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> AssignmentResponse:
    """
    Update an assignment.

    Can update title, description, due date, and active status.
    """
    # TODO: Implement assignment update
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Assignment not found"
    )


@router.delete(
    "/assignments/{assignment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete assignment",
    description="Delete an assignment."
)
async def delete_assignment(
    assignment_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Delete an assignment.

    This is a soft delete - the assignment is marked as inactive.
    """
    # TODO: Implement assignment deletion
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Assignment not found"
    )
