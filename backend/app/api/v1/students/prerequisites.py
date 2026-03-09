"""
Student Prerequisite Check API endpoint.

Allows students to check if they meet prerequisites before starting a paragraph.
"""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_student, get_current_user_school_id, get_student_from_user
from app.models.user import User
from app.models.student import Student
from app.schemas.prerequisite import PrerequisiteCheckResponse
from app.services.prerequisite_service import PrerequisiteService

router = APIRouter()


@router.get(
    "/paragraphs/{paragraph_id}/prerequisites",
    response_model=PrerequisiteCheckResponse,
)
async def check_paragraph_prerequisites(
    paragraph_id: int,
    current_user: User = Depends(require_student),
    school_id: int = Depends(get_current_user_school_id),
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Check if the student meets prerequisites for a paragraph.

    Returns warnings for unmet prerequisites with recommendations.
    `can_proceed` is False if any required prerequisite is unmet.
    """
    service = PrerequisiteService(db)
    return await service.check_prerequisites(student.id, paragraph_id)
