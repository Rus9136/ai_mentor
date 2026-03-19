"""
Student Lab API — interactive laboratory endpoints.

Endpoints:
- GET  /lab/available           — list available labs
- GET  /lab/{lab_id}            — get lab details
- GET  /lab/{lab_id}/progress   — get student progress
- POST /lab/{lab_id}/progress   — update progress
- GET  /lab/{lab_id}/tasks      — list tasks
- POST /lab/{lab_id}/tasks/{task_id}/answer — submit answer
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_student_from_user
from app.core.database import get_db
from app.models.student import Student
from app.schemas.lab import (
    LabResponse,
    LabProgressResponse,
    LabTaskResponse,
    LabTaskAnswerResult,
    ProgressUpdateRequest,
    TaskAnswerRequest,
)
from app.services.lab_service import LabService

router = APIRouter(prefix="/lab")


@router.get("/available", response_model=list[LabResponse])
async def get_available_labs(
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of available labs for the current student."""
    service = LabService(db)
    labs = await service.get_available_labs(school_id=student.school_id)
    return labs


@router.get("/{lab_id}", response_model=LabResponse)
async def get_lab(
    lab_id: int,
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get lab details."""
    service = LabService(db)
    return await service.get_lab(lab_id)


@router.get("/{lab_id}/progress", response_model=LabProgressResponse | None)
async def get_lab_progress(
    lab_id: int,
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get student's progress in a lab."""
    service = LabService(db)
    return await service.get_progress(student.id, lab_id)


@router.post("/{lab_id}/progress", response_model=LabProgressResponse)
async def update_lab_progress(
    lab_id: int,
    body: ProgressUpdateRequest,
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Update student's progress in a lab."""
    service = LabService(db)
    return await service.update_progress(student.id, lab_id, body.progress_data)


@router.get("/{lab_id}/tasks", response_model=list[LabTaskResponse])
async def get_lab_tasks(
    lab_id: int,
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Get list of tasks for a lab."""
    service = LabService(db)
    return await service.get_tasks(lab_id)


@router.post("/{lab_id}/tasks/{task_id}/answer", response_model=LabTaskAnswerResult)
async def submit_task_answer(
    lab_id: int,
    task_id: int,
    body: TaskAnswerRequest,
    student: Student = Depends(get_student_from_user),
    db: AsyncSession = Depends(get_db),
):
    """Submit an answer to a lab task."""
    service = LabService(db)
    result = await service.submit_answer(student.id, lab_id, task_id, body.answer_data)
    return LabTaskAnswerResult(**result)
