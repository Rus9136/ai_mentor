"""
Script to fix homework status for completed assignments.

Finds all HomeworkStudent records with status IN_PROGRESS where all tasks
are actually completed, and updates them to SUBMITTED.

Usage:
    docker exec -it ai_mentor_backend_prod python scripts/fix_homework_status.py
"""
import asyncio
import sys
from datetime import datetime, timezone

# Add parent directory to path
sys.path.insert(0, "/app")

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkStudent,
    HomeworkStudentStatus,
    StudentTaskSubmission,
    TaskSubmissionStatus,
)


async def fix_homework_statuses():
    """Fix homework statuses for completed assignments."""

    # Create async engine
    engine = create_async_engine(settings.async_database_url, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as db:
        # Find all HomeworkStudent with IN_PROGRESS status
        result = await db.execute(
            select(HomeworkStudent)
            .where(
                HomeworkStudent.status == HomeworkStudentStatus.IN_PROGRESS,
                HomeworkStudent.is_deleted == False
            )
        )
        in_progress_assignments = result.scalars().all()

        print(f"Found {len(in_progress_assignments)} homework assignments with IN_PROGRESS status")

        fixed_count = 0

        for hw_student in in_progress_assignments:
            # Get all tasks for this homework
            tasks_result = await db.execute(
                select(HomeworkTask.id)
                .where(
                    HomeworkTask.homework_id == hw_student.homework_id,
                    HomeworkTask.is_deleted == False
                )
            )
            task_ids = [row[0] for row in tasks_result.all()]

            if not task_ids:
                print(f"  Homework {hw_student.homework_id}: No tasks found, skipping")
                continue

            # For each task, check if there's a completed submission
            all_completed = True
            completed_statuses = {TaskSubmissionStatus.GRADED, TaskSubmissionStatus.NEEDS_REVIEW}

            for task_id in task_ids:
                # Get latest submission for this task
                sub_result = await db.execute(
                    select(StudentTaskSubmission)
                    .where(
                        StudentTaskSubmission.homework_student_id == hw_student.id,
                        StudentTaskSubmission.homework_task_id == task_id,
                        StudentTaskSubmission.is_deleted == False
                    )
                    .order_by(StudentTaskSubmission.attempt_number.desc())
                    .limit(1)
                )
                submission = sub_result.scalar_one_or_none()

                if not submission or submission.status not in completed_statuses:
                    all_completed = False
                    break

            if all_completed:
                # Update to SUBMITTED
                hw_student.status = HomeworkStudentStatus.SUBMITTED
                hw_student.submitted_at = hw_student.updated_at or datetime.now(timezone.utc)
                hw_student.updated_at = datetime.now(timezone.utc)
                fixed_count += 1
                print(f"  Fixed: Homework {hw_student.homework_id}, Student {hw_student.student_id} -> SUBMITTED")

        if fixed_count > 0:
            await db.commit()
            print(f"\nCommitted {fixed_count} fixes to database")
        else:
            print("\nNo fixes needed")

    await engine.dispose()


if __name__ == "__main__":
    print("=" * 50)
    print("Fixing homework statuses...")
    print("=" * 50)
    asyncio.run(fix_homework_statuses())
    print("Done!")
