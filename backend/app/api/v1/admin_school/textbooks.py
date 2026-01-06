"""
School Textbook Management API for ADMIN.
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id, get_pagination_params
from app.models.user import User
from app.models.textbook import Textbook
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.goso_repo import GosoRepository
from app.schemas.textbook import (
    TextbookCreate,
    TextbookUpdate,
    TextbookResponse,
    TextbookListResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from ._dependencies import get_textbook_for_school_admin, require_school_textbook


router = APIRouter(prefix="/textbooks", tags=["School Textbooks"])


@router.get("", response_model=PaginatedResponse[TextbookListResponse])
async def list_school_textbooks(
    include_global: bool = Query(True, description="Include global textbooks"),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Get textbooks for the school with pagination (ADMIN only).

    - **page**: Page number (1-indexed, default: 1)
    - **page_size**: Items per page (default: 20, max: 100)
    - **include_global**: Include global textbooks (default: true)
    """
    textbook_repo = TextbookRepository(db)

    textbooks, total = await textbook_repo.get_by_school_paginated(
        school_id=school_id,
        page=pagination.page,
        page_size=pagination.page_size,
        include_global=include_global,
    )

    return PaginatedResponse.create(
        items=textbooks,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
    )


@router.post("", response_model=TextbookResponse, status_code=status.HTTP_201_CREATED)
async def create_school_textbook(
    data: TextbookCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new school-specific textbook (ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    goso_repo = GosoRepository(db)

    # Validate subject_id
    subject = await goso_repo.get_subject_by_id(data.subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with ID {data.subject_id} not found"
        )

    # Create textbook with current school_id
    textbook_data = data.model_dump()
    textbook = Textbook(
        school_id=school_id,
        global_textbook_id=None,
        is_customized=False,
        version=1,
        subject=subject.name_ru,
        **textbook_data
    )

    return await textbook_repo.create(textbook)


@router.post("/{global_textbook_id}/customize", response_model=TextbookResponse, status_code=status.HTTP_201_CREATED)
async def customize_global_textbook(
    global_textbook_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Customize (fork) a global textbook for the school (ADMIN only).
    Creates a complete copy with all chapters and paragraphs.
    """
    textbook_repo = TextbookRepository(db)

    # Get global textbook
    source_textbook = await textbook_repo.get_by_id(global_textbook_id)
    if not source_textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {global_textbook_id} not found"
        )

    if source_textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only customize global textbooks (school_id = NULL)"
        )

    # Check if already customized
    existing = await textbook_repo.get_by_school(school_id, include_global=False)
    for textbook in existing:
        if textbook.global_textbook_id == global_textbook_id:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"School has already customized this textbook (ID: {textbook.id})"
            )

    # Fork textbook with all chapters and paragraphs
    forked_textbook = await textbook_repo.fork_textbook(source_textbook, school_id)

    return forked_textbook


@router.get("/{textbook_id}", response_model=TextbookResponse)
async def get_school_textbook(
    textbook: Textbook = Depends(get_textbook_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific textbook accessible to the school (ADMIN only).
    Can view both global and school-specific textbooks.
    """
    return textbook


@router.put("/{textbook_id}", response_model=TextbookResponse)
async def update_school_textbook(
    data: TextbookUpdate,
    textbook: Textbook = Depends(require_school_textbook),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a school-specific textbook (ADMIN only).
    Cannot update global textbooks.
    """
    textbook_repo = TextbookRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # If subject_id is being updated, validate and populate text field
    if "subject_id" in update_data and update_data["subject_id"] is not None:
        goso_repo = GosoRepository(db)
        subject = await goso_repo.get_subject_by_id(update_data["subject_id"])
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {update_data['subject_id']} not found"
            )
        update_data["subject"] = subject.name_ru

    for field, value in update_data.items():
        setattr(textbook, field, value)

    # Increment version on update
    textbook.version += 1

    return await textbook_repo.update(textbook)


@router.delete("/{textbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_textbook(
    textbook: Textbook = Depends(require_school_textbook),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a school-specific textbook (ADMIN only).
    Cannot delete global textbooks.
    """
    textbook_repo = TextbookRepository(db)
    await textbook_repo.soft_delete(textbook)
