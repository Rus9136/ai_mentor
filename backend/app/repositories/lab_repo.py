"""
Lab repository — CRUD operations for lab models.
"""
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.lab import Lab, LabProgress, LabTask, LabTaskAnswer


class LabRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Labs ---

    async def get_available_labs(self, school_id: Optional[int] = None) -> list[Lab]:
        """Get active labs: global (school_id=NULL) + school-specific."""
        query = (
            select(Lab)
            .where(Lab.is_active == True)  # noqa: E712
            .order_by(Lab.id)
        )
        if school_id:
            query = query.where(
                (Lab.school_id.is_(None)) | (Lab.school_id == school_id)
            )
        else:
            query = query.where(Lab.school_id.is_(None))

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_lab(self, lab_id: int) -> Optional[Lab]:
        result = await self.db.execute(
            select(Lab)
            .options(selectinload(Lab.tasks))
            .where(Lab.id == lab_id)
        )
        return result.scalar_one_or_none()

    # --- Progress ---

    async def get_progress(self, student_id: int, lab_id: int) -> Optional[LabProgress]:
        result = await self.db.execute(
            select(LabProgress).where(
                LabProgress.student_id == student_id,
                LabProgress.lab_id == lab_id,
            )
        )
        return result.scalar_one_or_none()

    async def upsert_progress(
        self, student_id: int, lab_id: int, progress_data: dict
    ) -> LabProgress:
        progress = await self.get_progress(student_id, lab_id)
        if progress:
            progress.progress_data = progress_data
        else:
            progress = LabProgress(
                student_id=student_id,
                lab_id=lab_id,
                progress_data=progress_data,
            )
            self.db.add(progress)
        await self.db.flush()
        return progress

    # --- Tasks ---

    async def get_tasks(self, lab_id: int) -> list[LabTask]:
        result = await self.db.execute(
            select(LabTask)
            .where(LabTask.lab_id == lab_id)
            .order_by(LabTask.order_index)
        )
        return list(result.scalars().all())

    async def get_task(self, task_id: int) -> Optional[LabTask]:
        result = await self.db.execute(
            select(LabTask).where(LabTask.id == task_id)
        )
        return result.scalar_one_or_none()

    # --- Task Answers ---

    async def get_answer(self, student_id: int, task_id: int) -> Optional[LabTaskAnswer]:
        result = await self.db.execute(
            select(LabTaskAnswer).where(
                LabTaskAnswer.student_id == student_id,
                LabTaskAnswer.lab_task_id == task_id,
            )
        )
        return result.scalar_one_or_none()

    async def create_answer(
        self,
        student_id: int,
        task_id: int,
        answer_data: dict,
        is_correct: bool,
        xp_earned: int,
    ) -> LabTaskAnswer:
        answer = LabTaskAnswer(
            student_id=student_id,
            lab_task_id=task_id,
            answer_data=answer_data,
            is_correct=is_correct,
            xp_earned=xp_earned,
        )
        self.db.add(answer)
        await self.db.flush()
        return answer
