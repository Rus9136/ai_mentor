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
    get_pagination_params,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.services.teacher_analytics import TeacherAnalyticsService
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.schemas.textbook import TextbookListResponse
from app.schemas.chapter import ChapterListResponse
from app.schemas.paragraph import ParagraphListResponse
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
    SelfAssessmentSummaryResponse,
    MetacognitiveAlertsResponse,
    StudentSelfAssessmentHistory,
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
    response_model=PaginatedResponse[TeacherClassResponse],
    summary="Get teacher's classes",
    description="Get list of all classes assigned to the current teacher. Supports pagination and filters."
)
async def get_classes(
    pagination: PaginationParams = Depends(get_pagination_params),
    academic_year: str = Query(None, description="Filter by academic year (e.g., '2025-2026')"),
    grade_level: int = Query(None, ge=1, le=11, description="Filter by grade level (1-11)"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[TeacherClassResponse]:
    """
    Get list of classes for the current teacher.

    Returns list of classes with:
    - Basic info (name, code, grade level)
    - Students count
    - Mastery distribution (A/B/C)
    - Average score and progress

    Filters:
    - academic_year: Filter by academic year (e.g., '2025-2026')
    - grade_level: Filter by grade level (1-11)
    """
    service = TeacherAnalyticsService(db)
    classes, total = await service.get_classes(
        current_user.id,
        school_id,
        page=pagination.page,
        page_size=pagination.page_size,
        academic_year=academic_year,
        grade_level=grade_level,
    )
    return PaginatedResponse.create(classes, total, pagination.page, pagination.page_size)


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
    response_model=PaginatedResponse[StrugglingTopicResponse],
    summary="Get struggling topics",
    description="Get topics where students are struggling (>30% in level C). Supports pagination."
)
async def get_struggling_topics(
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[StrugglingTopicResponse]:
    """
    Get topics where many students are struggling.

    Returns list of paragraphs ordered by struggling count:
    - Paragraph and chapter info
    - Number of struggling students
    - Percentage of students struggling
    - Average score

    Supports pagination with `page` and `page_size` query parameters.
    """
    service = TeacherAnalyticsService(db)
    topics, total = await service.get_struggling_topics(
        current_user.id,
        school_id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return PaginatedResponse.create(topics, total, pagination.page, pagination.page_size)


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


@router.get(
    "/analytics/self-assessment-summary",
    response_model=SelfAssessmentSummaryResponse,
    summary="Get self-assessment summary",
    description="Get aggregated self-assessment breakdown by paragraph for teacher's students."
)
async def get_self_assessment_summary(
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> SelfAssessmentSummaryResponse:
    service = TeacherAnalyticsService(db)
    return await service.get_self_assessment_summary(current_user.id, school_id)


@router.get(
    "/analytics/metacognitive-alerts",
    response_model=MetacognitiveAlertsResponse,
    summary="Get metacognitive alerts",
    description="Get students with overconfidence/underconfidence patterns."
)
async def get_metacognitive_alerts(
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> MetacognitiveAlertsResponse:
    service = TeacherAnalyticsService(db)
    return await service.get_metacognitive_alerts(current_user.id, school_id)


@router.get(
    "/students/{student_id}/self-assessments",
    response_model=StudentSelfAssessmentHistory,
    summary="Get student self-assessments",
    description="Get self-assessment history for a student."
)
async def get_student_self_assessments(
    student_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> StudentSelfAssessmentHistory:
    service = TeacherAnalyticsService(db)
    result = await service.get_student_self_assessments(
        current_user.id, school_id, student_id
    )
    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    return result


# ============================================================================
# CONTENT BROWSE (for ContentSelector in homework creation)
# ============================================================================

@router.get(
    "/textbooks",
    response_model=PaginatedResponse[TextbookListResponse],
    summary="Get textbooks for teacher",
    description="Get list of textbooks available to the teacher (global + school-specific). Supports pagination and filters."
)
async def list_textbooks_for_teacher(
    pagination: PaginationParams = Depends(get_pagination_params),
    subject_id: int = Query(None, description="Filter by subject ID"),
    grade_level: int = Query(None, ge=1, le=11, description="Filter by grade level (1-11)"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[TextbookListResponse]:
    """
    Get textbooks for content selection.

    Returns both global textbooks (school_id = NULL) and school-specific textbooks.
    Used by ContentSelector in homework creation.
    Supports pagination with `page` and `page_size` query parameters.

    Filters:
    - subject_id: Filter by subject ID
    - grade_level: Filter by grade level (1-11)
    """
    repo = TextbookRepository(db)
    textbooks, total = await repo.get_by_school_paginated(
        school_id,
        page=pagination.page,
        page_size=pagination.page_size,
        include_global=True,
        subject_id=subject_id,
        grade_level=grade_level,
    )
    return PaginatedResponse.create(textbooks, total, pagination.page, pagination.page_size)


@router.get(
    "/textbooks/{textbook_id}/chapters",
    response_model=PaginatedResponse[ChapterListResponse],
    summary="Get chapters for textbook",
    description="Get list of chapters in a textbook. Supports pagination."
)
async def list_chapters_for_teacher(
    textbook_id: int,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ChapterListResponse]:
    """
    Get chapters for a textbook.

    Validates that teacher has access to the textbook (global or their school).
    Supports pagination with `page` and `page_size` query parameters.
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Textbook not found"
        )

    # Check access: global textbooks (school_id=None) are accessible to all,
    # school-specific textbooks only to teachers from that school
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    chapter_repo = ChapterRepository(db)
    chapters, total = await chapter_repo.get_by_textbook_paginated(
        textbook_id, page=pagination.page, page_size=pagination.page_size
    )
    return PaginatedResponse.create(chapters, total, pagination.page, pagination.page_size)


@router.get(
    "/chapters/{chapter_id}/paragraphs",
    response_model=PaginatedResponse[ParagraphListResponse],
    summary="Get paragraphs for chapter",
    description="Get list of paragraphs in a chapter. Supports pagination."
)
async def list_paragraphs_for_teacher(
    chapter_id: int,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[ParagraphListResponse]:
    """
    Get paragraphs for a chapter.

    Validates access through parent textbook.
    Supports pagination with `page` and `page_size` query parameters.
    """
    chapter_repo = ChapterRepository(db)
    chapter = await chapter_repo.get_by_id(chapter_id)

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chapter not found"
        )

    # Check access via parent textbook
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)

    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    paragraph_repo = ParagraphRepository(db)
    paragraphs, total = await paragraph_repo.get_by_chapter_paginated(
        chapter_id, page=pagination.page, page_size=pagination.page_size
    )
    return PaginatedResponse.create(paragraphs, total, pagination.page, pagination.page_size)


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


# ============================================================================
# INVITATION CODES (for class join)
# ============================================================================

from app.repositories.invitation_code_repo import InvitationCodeRepository
from app.schemas.invitation_code import (
    InvitationCodeResponse,
    InvitationCodeCreate,
)


@router.get(
    "/classes/{class_id}/invitation-codes",
    response_model=List[InvitationCodeResponse],
    summary="Get class invitation codes",
    description="Get list of invitation codes for a specific class."
)
async def get_class_invitation_codes(
    class_id: int,
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> List[InvitationCodeResponse]:
    """
    Get invitation codes for a class.

    Teachers can only see codes for their own classes.
    """
    # Verify teacher has access to this class
    service = TeacherAnalyticsService(db)
    class_detail = await service.get_class_detail(current_user.id, school_id, class_id)

    if not class_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you don't have access to it"
        )

    code_repo = InvitationCodeRepository(db)
    codes = await code_repo.get_all(
        school_id=school_id,
        class_id=class_id,
        is_active=is_active,
        limit=100,
        offset=0,
    )

    result = []
    for code in codes:
        class_name = None
        if code.school_class:
            class_name = code.school_class.name

        created_by_name = None
        if code.creator:
            created_by_name = f"{code.creator.last_name} {code.creator.first_name}"

        result.append(InvitationCodeResponse(
            id=code.id,
            code=code.code,
            school_id=code.school_id,
            class_id=code.class_id,
            class_name=class_name,
            grade_level=code.grade_level,
            expires_at=code.expires_at,
            max_uses=code.max_uses,
            uses_count=code.uses_count,
            is_active=code.is_active,
            created_by=code.created_by,
            created_by_name=created_by_name,
            created_at=code.created_at,
            updated_at=code.updated_at,
        ))

    return result


@router.post(
    "/classes/{class_id}/invitation-codes",
    response_model=InvitationCodeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create class invitation code",
    description="Create a new invitation code for a class."
)
async def create_class_invitation_code(
    class_id: int,
    data: InvitationCodeCreate,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> InvitationCodeResponse:
    """
    Create an invitation code for a class.

    Teachers can create codes for their own classes.
    The code is automatically linked to the class and its grade level.
    """
    # Verify teacher has access to this class
    service = TeacherAnalyticsService(db)
    class_detail = await service.get_class_detail(current_user.id, school_id, class_id)

    if not class_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you don't have access to it"
        )

    code_repo = InvitationCodeRepository(db)

    try:
        code = await code_repo.create(
            school_id=school_id,
            grade_level=class_detail.grade_level,
            created_by=current_user.id,
            class_id=class_id,
            expires_at=data.expires_at,
            max_uses=data.max_uses,
            code_prefix=data.code_prefix or class_detail.name,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return InvitationCodeResponse(
        id=code.id,
        code=code.code,
        school_id=code.school_id,
        class_id=code.class_id,
        class_name=class_detail.name,
        grade_level=code.grade_level,
        expires_at=code.expires_at,
        max_uses=code.max_uses,
        uses_count=code.uses_count,
        is_active=code.is_active,
        created_by=code.created_by,
        created_by_name=f"{current_user.last_name} {current_user.first_name}",
        created_at=code.created_at,
        updated_at=code.updated_at,
    )


@router.delete(
    "/classes/{class_id}/invitation-codes/{code_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Deactivate class invitation code",
    description="Deactivate an invitation code (soft delete)."
)
async def deactivate_class_invitation_code(
    class_id: int,
    code_id: int,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> None:
    """
    Deactivate an invitation code.

    Teachers can only deactivate codes for their own classes.
    """
    # Verify teacher has access to this class
    service = TeacherAnalyticsService(db)
    class_detail = await service.get_class_detail(current_user.id, school_id, class_id)

    if not class_detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Class not found or you don't have access to it"
        )

    code_repo = InvitationCodeRepository(db)
    code = await code_repo.get_by_id(code_id, school_id)

    if not code or code.class_id != class_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation code not found"
        )

    await code_repo.deactivate(code)
