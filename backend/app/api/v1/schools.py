"""
Schools management API for SUPER_ADMIN.
Manages schools (tenants) in the multi-tenant system.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from app.core.database import get_db
from app.core.security import get_password_hash
from app.api.dependencies import require_super_admin
from app.models.user import User, UserRole
from app.models.school import School
from app.repositories.school_repo import SchoolRepository
from app.repositories.user_repo import UserRepository
from app.schemas.school import (
    SchoolCreate,
    SchoolUpdate,
    SchoolResponse,
    SchoolListResponse,
    SchoolAdminResponse,
    AdminPasswordReset,
)

router = APIRouter()


@router.get("/schools", response_model=List[SchoolListResponse])
async def list_schools(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all schools (SUPER_ADMIN only).
    Returns list of all schools ordered by creation date (newest first).
    """
    school_repo = SchoolRepository(db)
    return await school_repo.get_all()


@router.post(
    "/schools", response_model=SchoolResponse, status_code=status.HTTP_201_CREATED
)
async def create_school(
    data: SchoolCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new school (SUPER_ADMIN only).
    Optionally creates an admin user for the school in the same transaction.
    """
    school_repo = SchoolRepository(db)
    user_repo = UserRepository(db)

    # Check if code already exists
    existing_school = await school_repo.get_by_code(data.code)
    if existing_school:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"School with code '{data.code}' already exists",
        )

    # If admin provided, check email uniqueness
    if data.admin:
        existing_user = await user_repo.get_by_email(data.admin.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{data.admin.email}' already exists",
            )

    # Create school
    school_data = data.model_dump(exclude={"admin"})
    school = School(**school_data, is_active=True)
    db.add(school)

    try:
        await db.flush()  # Get school.id without committing
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"School with code '{data.code}' already exists",
        )

    # Create admin user if provided
    if data.admin:
        admin_user = User(
            email=data.admin.email,
            password_hash=get_password_hash(data.admin.password),
            first_name=data.admin.first_name,
            last_name=data.admin.last_name,
            middle_name=data.admin.middle_name,
            role=UserRole.ADMIN,
            school_id=school.id,
            is_active=True,
            is_verified=True,
        )
        db.add(admin_user)

        try:
            await db.flush()
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"User with email '{data.admin.email}' already exists",
            )

    await db.commit()
    await db.refresh(school)
    return school


@router.get("/schools/{school_id}", response_model=SchoolResponse)
async def get_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get a specific school by ID (SUPER_ADMIN only).
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    return school


@router.put("/schools/{school_id}", response_model=SchoolResponse)
async def update_school(
    school_id: int,
    data: SchoolUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Update a school (SUPER_ADMIN only).

    Note: School code cannot be updated after creation.
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(school, field, value)

    return await school_repo.update(school)


@router.delete("/schools/{school_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Soft delete a school (SUPER_ADMIN only).

    Sets is_deleted=True and deleted_at timestamp.
    This is a soft delete - data is not physically removed.
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)

    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    await school_repo.soft_delete(school)


@router.patch("/schools/{school_id}/block", response_model=SchoolResponse)
async def block_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Block a school (SUPER_ADMIN only).

    Sets is_active=False to prevent school users from accessing the system.
    """
    school_repo = SchoolRepository(db)

    try:
        school = await school_repo.block(school_id)
        return school
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch("/schools/{school_id}/unblock", response_model=SchoolResponse)
async def unblock_school(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Unblock a school (SUPER_ADMIN only).

    Sets is_active=True to restore school access.
    """
    school_repo = SchoolRepository(db)

    try:
        school = await school_repo.unblock(school_id)
        return school
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


# --- School Admin Management ---


@router.get("/schools/{school_id}/admins", response_model=List[SchoolAdminResponse])
async def get_school_admins(
    school_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Get all admin users for a school (SUPER_ADMIN only).
    """
    school_repo = SchoolRepository(db)
    school = await school_repo.get_by_id(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found",
        )

    result = await db.execute(
        select(User).where(
            User.school_id == school_id,
            User.role == UserRole.ADMIN.value,
            User.is_deleted == False,  # noqa: E712
        )
    )
    return list(result.scalars().all())


@router.post(
    "/schools/{school_id}/admins/{admin_id}/reset-password",
    response_model=SchoolAdminResponse,
)
async def reset_admin_password(
    school_id: int,
    admin_id: int,
    data: AdminPasswordReset,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Reset password for a school admin (SUPER_ADMIN only).
    """
    result = await db.execute(
        select(User).where(
            User.id == admin_id,
            User.school_id == school_id,
            User.role == UserRole.ADMIN.value,
            User.is_deleted == False,  # noqa: E712
        )
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Admin user not found for this school",
        )

    admin_user.password_hash = get_password_hash(data.password)
    await db.commit()
    await db.refresh(admin_user)
    return admin_user
