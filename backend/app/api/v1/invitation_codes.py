"""
Invitation code management endpoints for school admins.

Provides CRUD operations for invitation codes that students use
to register and bind to a school.
"""
from typing import Optional, List

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user, get_current_user_school_id, require_admin
from app.models.user import User
from app.repositories.invitation_code_repo import InvitationCodeRepository
from app.schemas.invitation_code import (
    InvitationCodeCreate,
    InvitationCodeUpdate,
    InvitationCodeResponse,
    InvitationCodeListResponse,
    InvitationCodeUseResponse,
)


router = APIRouter()


def _build_code_response(code, include_creator: bool = True) -> InvitationCodeResponse:
    """Build InvitationCodeResponse from model."""
    class_name = None
    if code.school_class:
        class_name = code.school_class.name

    created_by_name = None
    if include_creator and code.creator:
        created_by_name = f"{code.creator.last_name} {code.creator.first_name}"

    return InvitationCodeResponse(
        id=code.id,
        code=code.code,
        school_id=code.school_id,
        class_id=code.class_id,
        class_name=class_name,
        grade_level=code.grade_level,
        expires_at=code.expires_at,
        max_uses=code.max_uses,
        uses_count=code.uses_count,
        is_active=code.is_active,
        created_by=code.created_by,
        created_by_name=created_by_name,
        created_at=code.created_at,
        updated_at=code.updated_at,
    )


@router.get("", response_model=InvitationCodeListResponse)
async def list_invitation_codes(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    class_id: Optional[int] = Query(None, description="Filter by class ID"),
    grade_level: Optional[int] = Query(None, ge=1, le=11, description="Filter by grade level"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    school_id: int = Depends(get_current_user_school_id),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    List all invitation codes for the current school.

    Only accessible by school admins.
    """
    code_repo = InvitationCodeRepository(db)

    codes = await code_repo.get_all(
        school_id=school_id,
        is_active=is_active,
        class_id=class_id,
        grade_level=grade_level,
        limit=limit,
        offset=offset,
    )

    total = await code_repo.count(
        school_id=school_id,
        is_active=is_active,
        class_id=class_id,
        grade_level=grade_level,
    )

    return InvitationCodeListResponse(
        items=[_build_code_response(code) for code in codes],
        total=total,
    )


@router.post("", response_model=InvitationCodeResponse, status_code=status.HTTP_201_CREATED)
async def create_invitation_code(
    data: InvitationCodeCreate,
    school_id: int = Depends(get_current_user_school_id),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new invitation code.

    The code is automatically generated based on the optional prefix
    and random characters.

    Only accessible by school admins.
    """
    code_repo = InvitationCodeRepository(db)

    try:
        code = await code_repo.create(
            school_id=school_id,
            grade_level=data.grade_level,
            created_by=current_user.id,
            class_id=data.class_id,
            expires_at=data.expires_at,
            max_uses=data.max_uses,
            code_prefix=data.code_prefix,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )

    return _build_code_response(code, include_creator=False)


@router.get("/{code_id}", response_model=InvitationCodeResponse)
async def get_invitation_code(
    code_id: int,
    school_id: int = Depends(get_current_user_school_id),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific invitation code by ID.

    Only accessible by school admins.
    """
    code_repo = InvitationCodeRepository(db)
    code = await code_repo.get_by_id(code_id, school_id)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation code {code_id} not found"
        )

    return _build_code_response(code)


@router.patch("/{code_id}", response_model=InvitationCodeResponse)
async def update_invitation_code(
    code_id: int,
    data: InvitationCodeUpdate,
    school_id: int = Depends(get_current_user_school_id),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update an invitation code.

    Can update class_id, grade_level, expires_at, max_uses, and is_active.
    The code string itself cannot be changed.

    Only accessible by school admins.
    """
    code_repo = InvitationCodeRepository(db)
    code = await code_repo.get_by_id(code_id, school_id)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation code {code_id} not found"
        )

    # Update fields
    if data.class_id is not None:
        code.class_id = data.class_id
    if data.grade_level is not None:
        code.grade_level = data.grade_level
    if data.expires_at is not None:
        code.expires_at = data.expires_at
    if data.max_uses is not None:
        code.max_uses = data.max_uses
    if data.is_active is not None:
        code.is_active = data.is_active

    await code_repo.update(code)
    return _build_code_response(code)


@router.delete("/{code_id}", status_code=status.HTTP_204_NO_CONTENT)
async def deactivate_invitation_code(
    code_id: int,
    school_id: int = Depends(get_current_user_school_id),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Deactivate an invitation code.

    This does not delete the code, but marks it as inactive so it can no
    longer be used. The code and its usage history are preserved.

    Only accessible by school admins.
    """
    code_repo = InvitationCodeRepository(db)
    code = await code_repo.get_by_id(code_id, school_id)

    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation code {code_id} not found"
        )

    await code_repo.deactivate(code)
    return None


@router.get("/{code_id}/uses", response_model=List[InvitationCodeUseResponse])
async def list_invitation_code_uses(
    code_id: int,
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of results"),
    offset: int = Query(0, ge=0, description="Number of results to skip"),
    school_id: int = Depends(get_current_user_school_id),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get the list of students who used this invitation code.

    Returns usage history with student information.

    Only accessible by school admins.
    """
    code_repo = InvitationCodeRepository(db)

    # Verify code exists and belongs to school
    code = await code_repo.get_by_id(code_id, school_id)
    if not code:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invitation code {code_id} not found"
        )

    uses = await code_repo.get_uses(code_id, school_id, limit=limit, offset=offset)

    result = []
    for use in uses:
        student_name = None
        if use.student and use.student.user:
            student_name = f"{use.student.user.last_name} {use.student.user.first_name}"

        result.append(InvitationCodeUseResponse(
            id=use.id,
            invitation_code_id=use.invitation_code_id,
            student_id=use.student_id,
            student_name=student_name,
            created_at=use.created_at,
        ))

    return result
