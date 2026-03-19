"""
Student-facing API endpoints for coding challenges.

Routes:
  GET  /coding/topics                        — topics with progress
  GET  /coding/topics/{slug}/challenges      — challenges in topic
  GET  /coding/challenges/{id}               — challenge detail
  POST /coding/challenges/{id}/submit        — submit solution
  GET  /coding/challenges/{id}/submissions   — my attempts
  GET  /coding/stats                         — overall stats
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    require_student,
    get_current_user_school_id,
    get_student_from_user,
)
from app.models.user import User
from app.models.student import Student
from app.services.coding_service import CodingService, CodingServiceError
from app.schemas.coding import (
    TopicWithProgress,
    ChallengeListItem,
    ChallengeDetail,
    SubmissionCreate,
    SubmissionResponse,
    CodingStats,
)

router = APIRouter(prefix="/coding")


async def get_coding_service(db: AsyncSession = Depends(get_db)) -> CodingService:
    return CodingService(db)


# ---------------------------------------------------------------------------
# Topics
# ---------------------------------------------------------------------------

@router.get(
    "/topics",
    response_model=list[TopicWithProgress],
    summary="List coding topics with progress",
)
async def list_topics(
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CodingService = Depends(get_coding_service),
):
    return await service.list_topics_with_progress(student.id)


# ---------------------------------------------------------------------------
# Challenges
# ---------------------------------------------------------------------------

@router.get(
    "/topics/{slug}/challenges",
    response_model=list[ChallengeListItem],
    summary="List challenges in a topic",
)
async def list_challenges(
    slug: str,
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CodingService = Depends(get_coding_service),
):
    try:
        return await service.list_challenges(slug, student.id)
    except CodingServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get(
    "/challenges/{challenge_id}",
    response_model=ChallengeDetail,
    summary="Get challenge detail",
)
async def get_challenge(
    challenge_id: int,
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CodingService = Depends(get_coding_service),
):
    try:
        return await service.get_challenge_detail(challenge_id, student.id)
    except CodingServiceError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ---------------------------------------------------------------------------
# Submissions
# ---------------------------------------------------------------------------

@router.post(
    "/challenges/{challenge_id}/submit",
    response_model=SubmissionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit a solution",
)
async def submit_solution(
    challenge_id: int,
    data: SubmissionCreate,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    service: CodingService = Depends(get_coding_service),
):
    try:
        return await service.submit_solution(
            challenge_id=challenge_id,
            student_id=student.id,
            school_id=school_id,
            data=data,
        )
    except CodingServiceError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get(
    "/challenges/{challenge_id}/submissions",
    response_model=list[SubmissionResponse],
    summary="My attempts for a challenge",
)
async def list_submissions(
    challenge_id: int,
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CodingService = Depends(get_coding_service),
):
    return await service.list_submissions(challenge_id, student.id)


# ---------------------------------------------------------------------------
# Stats
# ---------------------------------------------------------------------------

@router.get(
    "/stats",
    response_model=CodingStats,
    summary="Coding practice statistics",
)
async def get_stats(
    current_user: User = Depends(require_student),
    student: Student = Depends(get_student_from_user),
    service: CodingService = Depends(get_coding_service),
):
    return await service.get_stats(student.id)
