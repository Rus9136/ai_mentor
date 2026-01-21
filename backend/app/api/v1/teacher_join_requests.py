"""
Teacher endpoints for student join request management.

This module provides endpoints for teachers to view and manage
student requests to join their classes.
"""
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.user import User
from app.api.dependencies import (
    require_teacher,
    get_current_user_school_id,
    get_pagination_params,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from app.schemas.join_request import (
    JoinRequestDetailResponse,
    JoinRequestApproveRequest,
    JoinRequestRejectRequest,
    JoinRequestActionResponse,
    PendingRequestCountResponse,
)
from app.services.join_request_service import JoinRequestService
from app.services.teacher_analytics.teacher_access_service import TeacherAccessService

router = APIRouter(prefix="/teachers/join-requests", tags=["teacher-join-requests"])


@router.get(
    "/pending-counts",
    response_model=List[PendingRequestCountResponse],
    summary="Get pending request counts for teacher's classes",
    description="Returns count of pending join requests for each class the teacher is assigned to."
)
async def get_pending_counts(
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> List[PendingRequestCountResponse]:
    """Get count of pending join requests per class for the teacher."""
    access_service = TeacherAccessService(db)
    teacher = await access_service.get_teacher_by_user_id(current_user.id, school_id)

    if not teacher:
        return []

    class_ids = await access_service.get_teacher_class_ids(teacher.id)
    if not class_ids:
        return []

    service = JoinRequestService(db)
    return await service.get_pending_counts_for_teacher(class_ids, school_id)


@router.get(
    "/classes/{class_id}",
    response_model=PaginatedResponse[JoinRequestDetailResponse],
    summary="Get pending requests for a class",
    description="Returns paginated list of pending join requests for a specific class."
)
async def get_class_pending_requests(
    class_id: int,
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> PaginatedResponse[JoinRequestDetailResponse]:
    """Get pending join requests for a specific class."""
    # Verify teacher has access to this class
    access_service = TeacherAccessService(db)
    teacher = await access_service.get_teacher_by_user_id(current_user.id, school_id)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher profile not found"
        )

    class_ids = await access_service.get_teacher_class_ids(teacher.id)
    if class_id not in class_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this class"
        )

    service = JoinRequestService(db)
    requests, total = await service.get_pending_for_class(
        class_id,
        school_id,
        page=pagination.page,
        page_size=pagination.page_size
    )

    return PaginatedResponse.create(
        requests, total, pagination.page, pagination.page_size
    )


@router.post(
    "/{request_id}/approve",
    response_model=JoinRequestActionResponse,
    summary="Approve a join request",
    description="Approves a student's request to join a class. The student will be added to the class."
)
async def approve_request(
    request_id: int,
    data: JoinRequestApproveRequest = None,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> JoinRequestActionResponse:
    """Approve a student join request."""
    # Verify teacher has access to the class in the request
    service = JoinRequestService(db)

    # First check if request exists and get its class_id
    request = await service._repo.get_by_id(request_id, school_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    # Verify teacher access
    access_service = TeacherAccessService(db)
    teacher = await access_service.get_teacher_by_user_id(current_user.id, school_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher profile not found"
        )

    class_ids = await access_service.get_teacher_class_ids(teacher.id)
    if request.class_id not in class_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this class"
        )

    result, error = await service.approve_request(request_id, current_user.id, school_id)

    if error:
        if error == "request_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        if error == "request_already_processed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This request has already been processed"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return result


@router.post(
    "/{request_id}/reject",
    response_model=JoinRequestActionResponse,
    summary="Reject a join request",
    description="Rejects a student's request to join a class. Optionally provide a reason."
)
async def reject_request(
    request_id: int,
    data: JoinRequestRejectRequest = None,
    current_user: User = Depends(require_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> JoinRequestActionResponse:
    """Reject a student join request."""
    # Verify teacher has access to the class in the request
    service = JoinRequestService(db)

    # First check if request exists and get its class_id
    request = await service._repo.get_by_id(request_id, school_id)
    if not request:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Request not found"
        )

    # Verify teacher access
    access_service = TeacherAccessService(db)
    teacher = await access_service.get_teacher_by_user_id(current_user.id, school_id)
    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Teacher profile not found"
        )

    class_ids = await access_service.get_teacher_class_ids(teacher.id)
    if request.class_id not in class_ids:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You don't have access to this class"
        )

    reason = data.reason if data else None
    result, error = await service.reject_request(
        request_id, current_user.id, school_id, reason
    )

    if error:
        if error == "request_not_found":
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Request not found"
            )
        if error == "request_already_processed":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="This request has already been processed"
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=error
        )

    return result
