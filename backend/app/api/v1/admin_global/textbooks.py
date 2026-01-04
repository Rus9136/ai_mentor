"""
Global Textbook CRUD endpoints for SUPER_ADMIN.
Manages global textbooks (school_id = NULL).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
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
from ._dependencies import require_global_textbook


router = APIRouter()


@router.post("/textbooks", response_model=TextbookResponse, status_code=status.HTTP_201_CREATED)
async def create_global_textbook(
    data: TextbookCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new global textbook (SUPER_ADMIN only).
    Global textbooks have school_id = NULL and are accessible to all schools.
    """
    textbook_repo = TextbookRepository(db)
    goso_repo = GosoRepository(db)

    # Validate subject_id exists
    subject = await goso_repo.get_subject_by_id(data.subject_id)
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Subject with ID {data.subject_id} not found"
        )

    # Create textbook with school_id = NULL (global)
    textbook_data = data.model_dump()
    textbook = Textbook(
        school_id=None,  # Global textbook
        global_textbook_id=None,
        is_customized=False,
        version=1,
        subject=subject.name_ru,  # Populate text field for backward compatibility
        **textbook_data
    )

    return await textbook_repo.create(textbook)


@router.get("/textbooks", response_model=List[TextbookListResponse])
async def list_global_textbooks(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all global textbooks (SUPER_ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    return await textbook_repo.get_all_global()


@router.get("/textbooks/{textbook_id}", response_model=TextbookResponse)
async def get_global_textbook(
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
):
    """
    Get a specific global textbook by ID (SUPER_ADMIN only).
    """
    return textbook


@router.put("/textbooks/{textbook_id}", response_model=TextbookResponse)
async def update_global_textbook(
    data: TextbookUpdate,
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a global textbook (SUPER_ADMIN only).
    Increments version number on update.
    """
    textbook_repo = TextbookRepository(db)
    goso_repo = GosoRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)

    # If subject_id is being updated, validate and update text field
    if "subject_id" in update_data and update_data["subject_id"] is not None:
        subject = await goso_repo.get_subject_by_id(update_data["subject_id"])
        if not subject:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Subject with ID {update_data['subject_id']} not found"
            )
        update_data["subject"] = subject.name_ru  # Update text field for backward compat

    for field, value in update_data.items():
        setattr(textbook, field, value)

    # Increment version on any update
    textbook.version += 1

    return await textbook_repo.update(textbook)


@router.delete("/textbooks/{textbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_textbook(
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a global textbook (SUPER_ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    await textbook_repo.soft_delete(textbook)
