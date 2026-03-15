"""
Quiz Battle report download endpoints (Phase 2.3).
Returns XLSX files via StreamingResponse.
"""
import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_teacher_from_user
from app.models.teacher import Teacher
from app.services.quiz_report_service import QuizReportService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/teachers/quiz-sessions", tags=["Teachers - Quiz Reports"])

XLSX_CONTENT_TYPE = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"


@router.get("/{session_id}/reports/class")
async def download_class_report(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Download class report as XLSX."""
    service = QuizReportService(db)
    try:
        output = await service.class_report(session_id, teacher.id)
        return StreamingResponse(
            output,
            media_type=XLSX_CONTENT_TYPE,
            headers={"Content-Disposition": f"attachment; filename=quiz_{session_id}_class.xlsx"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{session_id}/reports/questions")
async def download_question_report(
    session_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Download question analysis as XLSX."""
    service = QuizReportService(db)
    try:
        output = await service.question_report(session_id, teacher.id)
        return StreamingResponse(
            output,
            media_type=XLSX_CONTENT_TYPE,
            headers={"Content-Disposition": f"attachment; filename=quiz_{session_id}_questions.xlsx"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/reports/trend")
async def download_trend_report(
    class_id: int = Query(...),
    teacher: Teacher = Depends(get_teacher_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Download trend report as XLSX."""
    service = QuizReportService(db)
    try:
        output = await service.trend_report(class_id, teacher.id)
        return StreamingResponse(
            output,
            media_type=XLSX_CONTENT_TYPE,
            headers={"Content-Disposition": f"attachment; filename=quiz_trend_class_{class_id}.xlsx"},
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
