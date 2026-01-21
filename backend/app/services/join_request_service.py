"""
Service for student join request operations.
"""
import logging
from typing import List, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.models.student_join_request import StudentJoinRequest, JoinRequestStatus
from app.models.student import Student
from app.models.user import User
from app.repositories.join_request_repo import JoinRequestRepository
from app.repositories.school_class_repo import SchoolClassRepository
from app.repositories.invitation_code_repo import InvitationCodeRepository
from app.schemas.join_request import (
    JoinRequestDetailResponse,
    JoinRequestActionResponse,
    PendingRequestCountResponse,
    StudentJoinRequestStatusResponse,
)

logger = logging.getLogger(__name__)


class JoinRequestService:
    """Service for managing student join requests."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._repo = JoinRequestRepository(db)
        self._class_repo = SchoolClassRepository(db)
        self._code_repo = InvitationCodeRepository(db)

    async def create_request(
        self,
        student_id: int,
        class_id: int,
        school_id: int,
        invitation_code_id: Optional[int] = None
    ) -> Tuple[Optional[StudentJoinRequest], Optional[str]]:
        """
        Create a join request for a student.

        Args:
            student_id: ID of the student
            class_id: ID of the class to join
            school_id: School ID
            invitation_code_id: Optional invitation code ID

        Returns:
            Tuple of (request, error_message)
        """
        # Check for existing request
        existing = await self._repo.get_by_student_and_class(student_id, class_id)
        if existing:
            if existing.status == JoinRequestStatus.PENDING:
                return None, "request_already_pending"
            elif existing.status == JoinRequestStatus.APPROVED:
                return None, "already_in_class"
            # If rejected, allow new request by deleting old
            await self._repo.delete(existing)

        # Create request
        request = await self._repo.create(
            student_id=student_id,
            class_id=class_id,
            school_id=school_id,
            invitation_code_id=invitation_code_id
        )

        logger.info(f"Created join request {request.id} for student {student_id} to class {class_id}")
        return request, None

    async def create_request_by_code(
        self,
        student_id: int,
        invitation_code: str,
        first_name: str,
        last_name: str,
        middle_name: Optional[str] = None
    ) -> Tuple[Optional[StudentJoinRequest], Optional[str]]:
        """
        Create a join request using invitation code (from student profile).

        Validates the code, checks for existing pending requests,
        and creates a new request with FIO.

        Args:
            student_id: ID of the student
            invitation_code: The invitation code string
            first_name: Student's first name
            last_name: Student's last name
            middle_name: Student's middle name (optional)

        Returns:
            Tuple of (request, error_code)
            error_code can be: code_not_found, code_expired, code_exhausted,
                             code_inactive, request_pending, no_class
        """
        # Validate the invitation code
        is_valid, error_code, code = await self._code_repo.validate_code(invitation_code)

        if not is_valid:
            return None, error_code

        # Check if code has a class assigned
        if not code.class_id:
            return None, "no_class"

        # Check for existing pending request for this student
        existing_pending = await self._repo.get_student_pending_request(student_id)
        if existing_pending:
            return None, "request_pending"

        # Check for existing request for this specific class
        existing = await self._repo.get_by_student_and_class(student_id, code.class_id)
        if existing:
            if existing.status == JoinRequestStatus.PENDING:
                return None, "request_pending"
            elif existing.status == JoinRequestStatus.APPROVED:
                return None, "already_in_class"
            # If rejected, delete old request to allow new one
            await self._repo.delete(existing)

        # Create the join request with FIO
        request = await self._repo.create(
            student_id=student_id,
            class_id=code.class_id,
            school_id=code.school_id,
            invitation_code_id=code.id,
            first_name=first_name,
            last_name=last_name,
            middle_name=middle_name
        )

        logger.info(
            f"Created join request {request.id} for student {student_id} "
            f"to class {code.class_id} via code {invitation_code}"
        )
        return request, None

    async def get_pending_for_class(
        self,
        class_id: int,
        school_id: int,
        page: int = 1,
        page_size: int = 20
    ) -> Tuple[List[JoinRequestDetailResponse], int]:
        """Get pending requests for a class as detailed responses."""
        requests, total = await self._repo.get_pending_for_class(
            class_id, school_id, page, page_size
        )

        result = []
        for req in requests:
            result.append(JoinRequestDetailResponse(
                id=req.id,
                status=req.status.value,
                created_at=req.created_at,
                student_id=req.student.id,
                student_code=req.student.student_code,
                student_first_name=req.student.user.first_name,
                student_last_name=req.student.user.last_name,
                student_middle_name=req.student.user.middle_name,
                student_email=req.student.user.email,
                student_grade_level=req.student.grade_level,
                class_id=req.class_id,
                class_name=req.school_class.name if req.school_class else "",
                invitation_code=req.invitation_code.code if req.invitation_code else None
            ))

        return result, total

    async def approve_request(
        self,
        request_id: int,
        reviewer_id: int,
        school_id: int
    ) -> Tuple[Optional[JoinRequestActionResponse], Optional[str]]:
        """
        Approve a join request and add student to class.

        When approved:
        1. Update student's school_id to the new school
        2. Update student's FIO if provided in the request
        3. Remove student from all previous classes
        4. Add student to the new class
        5. Mark invitation code as used

        Args:
            request_id: ID of the request
            reviewer_id: ID of the user approving
            school_id: School ID for isolation

        Returns:
            Tuple of (response, error_message)
        """
        request = await self._repo.get_by_id(request_id, school_id)
        if not request:
            return None, "request_not_found"

        if request.status != JoinRequestStatus.PENDING:
            return None, "request_already_processed"

        # Get student with user for FIO update
        result = await self.db.execute(
            select(Student)
            .options(selectinload(Student.user))
            .where(Student.id == request.student_id)
        )
        student = result.scalar_one_or_none()

        if not student:
            return None, "student_not_found"

        old_school_id = student.school_id

        # 1. Update student's school_id
        student.school_id = request.school_id
        logger.info(
            f"Updating student {student.id} school_id from {old_school_id} "
            f"to {request.school_id}"
        )

        # 2. Update student's FIO if provided in request
        if request.first_name and student.user:
            student.user.first_name = request.first_name
        if request.last_name and student.user:
            student.user.last_name = request.last_name
        if request.middle_name is not None and student.user:
            student.user.middle_name = request.middle_name

        await self.db.commit()

        # 3. Remove student from all previous classes
        removed_count = await self._class_repo.remove_student_from_all_classes(
            student.id
        )
        if removed_count > 0:
            logger.info(
                f"Removed student {student.id} from {removed_count} previous classes"
            )

        # 4. Add student to new class
        try:
            await self._class_repo.add_students(
                request.class_id,
                [request.student_id],
                request.school_id  # Use request's school_id (new school)
            )
        except ValueError as e:
            logger.error(f"Failed to add student to class: {e}")
            return None, str(e)

        # 5. Mark code as used if present
        if request.invitation_code:
            try:
                await self._code_repo.use_code(
                    request.invitation_code,
                    request.student_id
                )
            except Exception as e:
                logger.warning(f"Failed to mark invitation code as used: {e}")

        # Approve request
        approved = await self._repo.approve(request, reviewer_id)

        logger.info(f"Approved join request {request_id} by user {reviewer_id}")

        return JoinRequestActionResponse(
            id=approved.id,
            status=approved.status.value,
            reviewed_at=approved.reviewed_at,
            message="Student successfully added to class"
        ), None

    async def reject_request(
        self,
        request_id: int,
        reviewer_id: int,
        school_id: int,
        reason: Optional[str] = None
    ) -> Tuple[Optional[JoinRequestActionResponse], Optional[str]]:
        """
        Reject a join request.

        Args:
            request_id: ID of the request
            reviewer_id: ID of the user rejecting
            school_id: School ID for isolation
            reason: Optional rejection reason

        Returns:
            Tuple of (response, error_message)
        """
        request = await self._repo.get_by_id(request_id, school_id)
        if not request:
            return None, "request_not_found"

        if request.status != JoinRequestStatus.PENDING:
            return None, "request_already_processed"

        rejected = await self._repo.reject(request, reviewer_id, reason)

        logger.info(f"Rejected join request {request_id} by user {reviewer_id}")

        return JoinRequestActionResponse(
            id=rejected.id,
            status=rejected.status.value,
            reviewed_at=rejected.reviewed_at,
            message="Request rejected"
        ), None

    async def get_pending_counts_for_teacher(
        self,
        class_ids: List[int],
        school_id: int
    ) -> List[PendingRequestCountResponse]:
        """
        Get pending request counts for teacher's classes.

        Args:
            class_ids: List of class IDs the teacher has access to
            school_id: School ID

        Returns:
            List of counts with class info
        """
        if not class_ids:
            return []

        counts = await self._repo.get_pending_counts_for_classes(class_ids, school_id)

        result = []
        for count_info in counts:
            if count_info["pending_count"] > 0:
                school_class = await self._class_repo.get_by_id(
                    count_info["class_id"], school_id
                )
                if school_class:
                    result.append(PendingRequestCountResponse(
                        class_id=count_info["class_id"],
                        class_name=school_class.name,
                        pending_count=count_info["pending_count"]
                    ))

        return result

    async def get_student_pending_status(
        self,
        student_id: int
    ) -> dict:
        """
        Get student's pending request status.

        Args:
            student_id: Student ID

        Returns:
            Dict with pending status info
        """
        pending = await self._repo.get_student_pending_request(student_id)

        if pending:
            return {
                "has_pending_request": True,
                "class_name": pending.school_class.name if pending.school_class else None,
                "class_id": pending.class_id,
                "created_at": pending.created_at
            }
        return {
            "has_pending_request": False,
            "class_name": None,
            "class_id": None,
            "created_at": None
        }

    async def get_student_request_status(
        self,
        student_id: int
    ) -> StudentJoinRequestStatusResponse:
        """
        Get student's latest join request status (for profile display).

        Returns the most recent request that is pending or rejected.

        Args:
            student_id: Student ID

        Returns:
            StudentJoinRequestStatusResponse with request details or empty response
        """
        request = await self._repo.get_student_latest_request(student_id)

        if not request:
            return StudentJoinRequestStatusResponse(has_request=False)

        return StudentJoinRequestStatusResponse(
            id=request.id,
            status=request.status.value,
            class_name=request.school_class.name if request.school_class else None,
            school_name=request.school.name if request.school else None,
            created_at=request.created_at,
            rejection_reason=request.rejection_reason,
            has_request=True
        )
