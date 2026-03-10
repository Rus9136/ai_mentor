"""
Student usage endpoints (read-only).
Shows remaining messages for the current day.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_student_from_user, get_current_user_school_id
from app.models.student import Student
from app.services.usage_limit_service import UsageLimitService
from app.schemas.subscription import UsageSummaryResponse

router = APIRouter(prefix="/usage")


@router.get("/today", response_model=UsageSummaryResponse)
async def get_today_usage(
    student: Student = Depends(get_student_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Get current student's usage summary for today with plan limits."""
    service = UsageLimitService(db)
    return await service.get_user_summary(
        user_id=student.user_id,
        school_id=school_id,
    )
