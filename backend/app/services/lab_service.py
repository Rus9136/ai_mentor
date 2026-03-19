"""
Lab service — business logic for interactive laboratories.
"""
from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.lab import Lab, LabProgress, LabTask
from app.repositories.lab_repo import LabRepository


class LabService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = LabRepository(db)

    async def get_available_labs(self, school_id: Optional[int] = None) -> list[Lab]:
        return await self.repo.get_available_labs(school_id)

    async def get_lab(self, lab_id: int) -> Lab:
        lab = await self.repo.get_lab(lab_id)
        if not lab:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lab not found",
            )
        return lab

    async def get_progress(self, student_id: int, lab_id: int) -> Optional[LabProgress]:
        return await self.repo.get_progress(student_id, lab_id)

    async def update_progress(
        self, student_id: int, lab_id: int, progress_data: dict
    ) -> LabProgress:
        # Verify lab exists
        await self.get_lab(lab_id)
        progress = await self.repo.upsert_progress(student_id, lab_id, progress_data)
        await self.db.commit()
        return progress

    async def get_tasks(self, lab_id: int) -> list[LabTask]:
        # Verify lab exists
        await self.get_lab(lab_id)
        return await self.repo.get_tasks(lab_id)

    async def submit_answer(
        self, student_id: int, lab_id: int, task_id: int, answer_data: dict
    ) -> dict:
        """Submit answer to a lab task. Returns result with correctness and XP."""
        # Verify lab exists
        await self.get_lab(lab_id)

        # Get task
        task = await self.repo.get_task(task_id)
        if not task or task.lab_id != lab_id:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Task not found in this lab",
            )

        # Check if already answered
        existing = await self.repo.get_answer(student_id, task_id)
        if existing:
            return {
                "is_correct": existing.is_correct,
                "explanation": task.task_data.get("explanation"),
                "xp_earned": 0,  # No XP for repeat answers
            }

        # Check answer
        is_correct = self._check_answer(task, answer_data)
        xp_earned = task.xp_reward if is_correct else 0

        # Save answer
        await self.repo.create_answer(
            student_id=student_id,
            task_id=task_id,
            answer_data=answer_data,
            is_correct=is_correct,
            xp_earned=xp_earned,
        )

        # Update progress XP
        if xp_earned > 0:
            progress = await self.repo.get_progress(student_id, lab_id)
            if progress:
                progress.xp_earned = (progress.xp_earned or 0) + xp_earned
            else:
                await self.repo.upsert_progress(
                    student_id, lab_id, {"tasks_completed": 1}
                )
                progress = await self.repo.get_progress(student_id, lab_id)
                if progress:
                    progress.xp_earned = xp_earned

        await self.db.commit()

        return {
            "is_correct": is_correct,
            "explanation": task.task_data.get("explanation"),
            "xp_earned": xp_earned,
        }

    @staticmethod
    def _check_answer(task: LabTask, answer_data: dict) -> bool:
        """Check if student's answer is correct based on task type."""
        task_data = task.task_data or {}
        correct_answer = task_data.get("correct_answer")

        if correct_answer is None:
            return False

        task_type = task.task_type

        if task_type == "quiz":
            # Simple option comparison
            return answer_data.get("selected") == correct_answer

        if task_type == "choose_epoch":
            return answer_data.get("epoch_id") == correct_answer

        if task_type == "order_events":
            # Check if ordering matches
            return answer_data.get("order") == correct_answer

        if task_type == "find_on_map":
            # Check if click coordinates are within tolerance
            target = correct_answer  # {lat, lng}
            click = answer_data.get("coordinates", {})
            if not click or "lat" not in click or "lng" not in click:
                return False
            tolerance = task_data.get("tolerance", 2.0)  # degrees
            lat_diff = abs(float(click["lat"]) - float(target["lat"]))
            lng_diff = abs(float(click["lng"]) - float(target["lng"]))
            return lat_diff <= tolerance and lng_diff <= tolerance

        return False
