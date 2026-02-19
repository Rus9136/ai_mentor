"""
Repository for HomeworkStudent (assignment) operations.
"""
from typing import Optional, List, Tuple
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.homework import (
    Homework,
    HomeworkTask,
    HomeworkTaskQuestion,
    HomeworkStudent,
    HomeworkStatus,
    HomeworkStudentStatus,
)


class StudentAssignmentRepository:
    """Repository for student homework assignments."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def assign_to_students(
        self,
        homework_id: int,
        school_id: int,
        student_ids: List[int]
    ) -> List[HomeworkStudent]:
        """Assign homework to students."""
        assignments = []
        for student_id in student_ids:
            existing = await self.db.execute(
                select(HomeworkStudent).where(
                    HomeworkStudent.homework_id == homework_id,
                    HomeworkStudent.student_id == student_id
                )
            )
            if existing.scalar_one_or_none():
                continue

            assignment = HomeworkStudent(
                homework_id=homework_id,
                student_id=student_id,
                school_id=school_id,
                status=HomeworkStudentStatus.ASSIGNED
            )
            self.db.add(assignment)
            assignments.append(assignment)

        await self.db.flush()
        for a in assignments:
            await self.db.refresh(a)
        return assignments

    async def get_student_homework(
        self,
        homework_id: int,
        student_id: int
    ) -> Optional[HomeworkStudent]:
        """Get student's homework assignment."""
        result = await self.db.execute(
            select(HomeworkStudent)
            .options(
                selectinload(HomeworkStudent.task_submissions),
                selectinload(HomeworkStudent.homework),
            )
            .where(
                HomeworkStudent.homework_id == homework_id,
                HomeworkStudent.student_id == student_id,
                HomeworkStudent.is_deleted == False
            )
        )
        return result.unique().scalar_one_or_none()

    async def list_student_homework(
        self,
        student_id: int,
        school_id: int,
        status: Optional[HomeworkStudentStatus] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> Tuple[List[HomeworkStudent], int]:
        """
        List homework assigned to a student with pagination.

        Args:
            student_id: Student ID
            school_id: School ID
            status: Filter by status (optional)
            page: Page number (1-based)
            page_size: Number of items per page

        Returns:
            Tuple of (list of homework assignments, total count)
        """
        # Base query filters
        base_filters = [
            HomeworkStudent.student_id == student_id,
            HomeworkStudent.school_id == school_id,
            HomeworkStudent.is_deleted == False
        ]
        if status:
            base_filters.append(HomeworkStudent.status == status)

        # Build base query with join
        base_query = (
            select(HomeworkStudent)
            .join(Homework)
            .where(
                *base_filters,
                Homework.status == HomeworkStatus.PUBLISHED,
                Homework.is_deleted == False
            )
        )

        # Get total count
        count_query = select(func.count()).select_from(base_query.subquery())
        total = (await self.db.execute(count_query)).scalar() or 0

        # Get paginated results with eager loading
        offset = (page - 1) * page_size
        query = (
            base_query
            .options(
                selectinload(HomeworkStudent.homework)
                .selectinload(Homework.tasks.and_(
                    HomeworkTask.is_deleted == False
                ))
                .selectinload(HomeworkTask.questions.and_(
                    HomeworkTaskQuestion.is_deleted == False
                ))
            )
            .order_by(Homework.due_date.asc())
            .offset(offset)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return list(result.unique().scalars().all()), total

    async def update_student_homework_status(
        self,
        homework_student_id: int,
        status: HomeworkStudentStatus
    ) -> Optional[HomeworkStudent]:
        """Update student homework status."""
        result = await self.db.execute(
            select(HomeworkStudent).where(HomeworkStudent.id == homework_student_id)
        )
        hw_student = result.scalar_one_or_none()
        if hw_student:
            hw_student.status = status
            hw_student.updated_at = datetime.utcnow()
            await self.db.flush()
        return hw_student
