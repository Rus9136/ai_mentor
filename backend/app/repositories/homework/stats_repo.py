"""
Repository for Homework statistics and AI logging.
"""
from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.homework import (
    HomeworkStudent,
    HomeworkStudentStatus,
    AIGenerationLog,
)


class HomeworkStatsRepository:
    """Repository for homework statistics and aggregations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_homework_stats(
        self,
        homework_id: int,
        school_id: int
    ) -> dict:
        """Get statistics for a homework."""
        # Total students
        total_result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkStudent)
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.is_deleted == False
            )
        )
        total_students = total_result.scalar() or 0

        # Submitted count
        submitted_result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkStudent)
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.status.in_([
                    HomeworkStudentStatus.SUBMITTED,
                    HomeworkStudentStatus.GRADED
                ]),
                HomeworkStudent.is_deleted == False
            )
        )
        submitted_count = submitted_result.scalar() or 0

        # Graded count
        graded_result = await self.db.execute(
            select(func.count())
            .select_from(HomeworkStudent)
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.status == HomeworkStudentStatus.GRADED,
                HomeworkStudent.is_deleted == False
            )
        )
        graded_count = graded_result.scalar() or 0

        # Average score
        avg_result = await self.db.execute(
            select(func.avg(HomeworkStudent.percentage))
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.percentage.isnot(None),
                HomeworkStudent.is_deleted == False
            )
        )
        average_score = avg_result.scalar()

        return {
            "total_students": total_students,
            "submitted_count": submitted_count,
            "graded_count": graded_count,
            "average_score": round(average_score, 2) if average_score else None
        }

    async def log_ai_operation(
        self,
        operation_type: str,
        school_id: Optional[int] = None,
        teacher_id: Optional[int] = None,
        homework_id: Optional[int] = None,
        task_id: Optional[int] = None,
        student_id: Optional[int] = None,
        input_context: Optional[dict] = None,
        prompt_used: Optional[str] = None,
        model_used: Optional[str] = None,
        raw_response: Optional[str] = None,
        parsed_output: Optional[dict] = None,
        tokens_input: Optional[int] = None,
        tokens_output: Optional[int] = None,
        latency_ms: Optional[int] = None,
        success: bool = True,
        error_message: Optional[str] = None
    ) -> AIGenerationLog:
        """Log an AI operation for auditing."""
        log = AIGenerationLog(
            operation_type=operation_type,
            school_id=school_id,
            teacher_id=teacher_id,
            homework_id=homework_id,
            homework_task_id=task_id,
            student_id=student_id,
            input_context=input_context,
            prompt_used=prompt_used,
            model_used=model_used,
            raw_response=raw_response,
            parsed_output=parsed_output,
            tokens_input=tokens_input,
            tokens_output=tokens_output,
            latency_ms=latency_ms,
            success=success,
            error_message=error_message
        )
        self.db.add(log)
        await self.db.flush()
        await self.db.refresh(log)
        return log
