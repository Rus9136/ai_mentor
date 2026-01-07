"""
Global Chapter CRUD endpoints for SUPER_ADMIN.
Manages chapters in global textbooks (school_id = NULL).
"""

from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin, get_pagination_params
from app.models.user import User
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.repositories.chapter_repo import ChapterRepository
from app.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterListResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from ._dependencies import require_global_textbook, require_global_chapter


router = APIRouter()


@router.post("/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_global_chapter(
    data: ChapterCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chapter in a global textbook (SUPER_ADMIN only).
    """
    # Verify textbook exists and is global using dependency logic
    from app.repositories.textbook_repo import TextbookRepository
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)

    textbook = await textbook_repo.get_by_id(data.textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {data.textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add chapter to non-global textbook. Use school admin endpoints."
        )

    # Create chapter
    chapter = Chapter(**data.model_dump())
    return await chapter_repo.create(chapter)


@router.get("/textbooks/{textbook_id}/chapters", response_model=PaginatedResponse[ChapterListResponse])
async def list_global_chapters(
    textbook: Textbook = Depends(require_global_textbook),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chapters for a global textbook (SUPER_ADMIN only).

    Supports pagination with `page` and `page_size` query parameters.
    """
    chapter_repo = ChapterRepository(db)
    chapters, total = await chapter_repo.get_by_textbook_paginated(
        textbook_id=textbook.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return PaginatedResponse.create(chapters, total, pagination.page, pagination.page_size)


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_global_chapter(
    chapter_and_textbook: Tuple[Chapter, Textbook] = Depends(require_global_chapter),
    current_user: User = Depends(require_super_admin),
):
    """
    Get a single chapter from a global textbook (SUPER_ADMIN only).
    """
    chapter, _ = chapter_and_textbook
    return chapter


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_global_chapter(
    data: ChapterUpdate,
    chapter_and_textbook: Tuple[Chapter, Textbook] = Depends(require_global_chapter),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a chapter in a global textbook (SUPER_ADMIN only).
    """
    chapter, _ = chapter_and_textbook
    chapter_repo = ChapterRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chapter, field, value)

    return await chapter_repo.update(chapter)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_chapter(
    chapter_and_textbook: Tuple[Chapter, Textbook] = Depends(require_global_chapter),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a chapter in a global textbook (SUPER_ADMIN only).
    """
    chapter, _ = chapter_and_textbook
    chapter_repo = ChapterRepository(db)
    await chapter_repo.soft_delete(chapter)
