"""
Repository for StudentJoinRequest data access.
"""
from datetime import datetime, timezone
from typing import Optional, List, Tuple

from sqlalchemy import select, and_, func, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.student_join_request import StudentJoinRequest, JoinRequestStatus
from app.models.student import Student
from app.models.user import User
from app.models.school_class import SchoolClass


class JoinRequestRepository:
    """Repository for StudentJoinRequest CRUD operations."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(
        self,
        request_id: int,
        school_id: int,
        load_student: bool = True,
        load_class: bool = True
    ) -> Optional[StudentJoinRequest]:
        """Get join request by ID with school isolation."""
        query = select(StudentJoinRequest).where(
            StudentJoinRequest.id == request_id,
            StudentJoinRequest.school_id == school_id
        )

        if load_student:
            query = query.options(
                selectinload(StudentJoinRequest.student)
                .selectinload(Student.user)
            )
        if load_class:
            query = query.options(selectinload(StudentJoinRequest.school_class))

        result = await self.db.execute(query)
        return result.scalar_one_or_none()

    async def get_pending_for_class(
        self,
        class_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[StudentJoinRequest], int]:
        """Get pending requests for a specific class with pagination."""
        filters = [
            StudentJoinRequest.class_id == class_id,
            StudentJoinRequest.school_id == school_id,
            StudentJoinRequest.status == JoinRequestStatus.PENDING
        ]

        # Count query
        count_query = select(func.count(StudentJoinRequest.id)).where(and_(*filters))
        total = (await self.db.execute(count_query)).scalar() or 0

        # Main query with eager loading
        query = (
            select(StudentJoinRequest)
            .options(
                selectinload(StudentJoinRequest.student).selectinload(Student.user),
                selectinload(StudentJoinRequest.school_class),
                selectinload(StudentJoinRequest.invitation_code)
            )
            .where(and_(*filters))
            .order_by(StudentJoinRequest.created_at.asc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )

        result = await self.db.execute(query)
        return list(result.scalars().all()), total

    async def get_pending_count_for_class(
        self,
        class_id: int,
        school_id: int
    ) -> int:
        """Get count of pending requests for a class."""
        result = await self.db.execute(
            select(func.count(StudentJoinRequest.id)).where(
                StudentJoinRequest.class_id == class_id,
                StudentJoinRequest.school_id == school_id,
                StudentJoinRequest.status == JoinRequestStatus.PENDING
            )
        )
        return result.scalar() or 0

    async def get_pending_counts_for_classes(
        self,
        class_ids: List[int],
        school_id: int
    ) -> List[dict]:
        """
        Get pending request counts for multiple classes.
        Returns list of {class_id, pending_count}.
        """
        if not class_ids:
            return []

        query = (
            select(
                StudentJoinRequest.class_id,
                func.count(StudentJoinRequest.id).label('pending_count')
            )
            .where(
                StudentJoinRequest.class_id.in_(class_ids),
                StudentJoinRequest.school_id == school_id,
                StudentJoinRequest.status == JoinRequestStatus.PENDING
            )
            .group_by(StudentJoinRequest.class_id)
        )

        result = await self.db.execute(query)
        rows = result.all()

        return [
            {"class_id": row.class_id, "pending_count": row.pending_count}
            for row in rows
        ]

    async def get_pending_for_teacher_classes(
        self,
        class_ids: List[int],
        school_id: int
    ) -> List[StudentJoinRequest]:
        """Get all pending requests for teacher's classes."""
        if not class_ids:
            return []

        query = (
            select(StudentJoinRequest)
            .options(
                selectinload(StudentJoinRequest.student).selectinload(Student.user),
                selectinload(StudentJoinRequest.school_class),
                selectinload(StudentJoinRequest.invitation_code)
            )
            .where(
                StudentJoinRequest.class_id.in_(class_ids),
                StudentJoinRequest.school_id == school_id,
                StudentJoinRequest.status == JoinRequestStatus.PENDING
            )
            .order_by(StudentJoinRequest.created_at.asc())
        )

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_by_student_and_class(
        self,
        student_id: int,
        class_id: int
    ) -> Optional[StudentJoinRequest]:
        """Get existing request for student-class combination."""
        result = await self.db.execute(
            select(StudentJoinRequest).where(
                StudentJoinRequest.student_id == student_id,
                StudentJoinRequest.class_id == class_id
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self,
        student_id: int,
        class_id: int,
        school_id: int,
        invitation_code_id: Optional[int] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        middle_name: Optional[str] = None
    ) -> StudentJoinRequest:
        """Create a new join request with optional FIO."""
        request = StudentJoinRequest(
            student_id=student_id,
            class_id=class_id,
            school_id=school_id,
            invitation_code_id=invitation_code_id,
            status=JoinRequestStatus.PENDING,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name
        )
        self.db.add(request)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def approve(
        self,
        request: StudentJoinRequest,
        reviewer_id: int
    ) -> StudentJoinRequest:
        """Approve a join request."""
        request.status = JoinRequestStatus.APPROVED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def reject(
        self,
        request: StudentJoinRequest,
        reviewer_id: int,
        reason: Optional[str] = None
    ) -> StudentJoinRequest:
        """Reject a join request."""
        request.status = JoinRequestStatus.REJECTED
        request.reviewed_by = reviewer_id
        request.reviewed_at = datetime.now(timezone.utc)
        request.rejection_reason = reason
        await self.db.commit()
        await self.db.refresh(request)
        return request

    async def get_student_pending_request(
        self,
        student_id: int
    ) -> Optional[StudentJoinRequest]:
        """Get student's pending request (for status check)."""
        result = await self.db.execute(
            select(StudentJoinRequest)
            .options(selectinload(StudentJoinRequest.school_class))
            .where(
                StudentJoinRequest.student_id == student_id,
                StudentJoinRequest.status == JoinRequestStatus.PENDING
            )
        )
        return result.scalar_one_or_none()

    async def delete(self, request: StudentJoinRequest) -> None:
        """Delete a join request (used when replacing rejected request)."""
        await self.db.delete(request)
        await self.db.commit()

    async def get_student_latest_request(
        self,
        student_id: int
    ) -> Optional[StudentJoinRequest]:
        """
        Get student's latest join request (pending or rejected).

        Returns the most recent request regardless of status (except approved).
        Used to show current status in student profile.
        """
        result = await self.db.execute(
            select(StudentJoinRequest)
            .options(
                selectinload(StudentJoinRequest.school_class),
                selectinload(StudentJoinRequest.school)
            )
            .where(
                StudentJoinRequest.student_id == student_id,
                StudentJoinRequest.status.in_([
                    JoinRequestStatus.PENDING,
                    JoinRequestStatus.REJECTED
                ])
            )
            .order_by(StudentJoinRequest.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()
