"""
Global Paragraph CRUD endpoints for SUPER_ADMIN.
Manages paragraphs in global textbooks (school_id = NULL).
"""

from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin, get_pagination_params
from app.models.user import User
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.textbook_repo import TextbookRepository
from app.schemas.paragraph import (
    ParagraphCreate,
    ParagraphUpdate,
    ParagraphResponse,
    ParagraphListResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams
from ._dependencies import require_global_chapter, require_global_paragraph


router = APIRouter()


@router.post("/paragraphs", response_model=ParagraphResponse, status_code=status.HTTP_201_CREATED)
async def create_global_paragraph(
    data: ParagraphCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new paragraph in a global chapter (SUPER_ADMIN only).
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)
    paragraph_repo = ParagraphRepository(db)

    # Verify chapter exists and belongs to global textbook
    chapter = await chapter_repo.get_by_id(data.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {data.chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add paragraph to non-global chapter. Use school admin endpoints."
        )

    # Create paragraph
    paragraph = Paragraph(**data.model_dump())
    return await paragraph_repo.create(paragraph)


@router.get("/chapters/{chapter_id}/paragraphs", response_model=PaginatedResponse[ParagraphListResponse])
async def list_global_paragraphs(
    chapter_and_textbook: Tuple[Chapter, Textbook] = Depends(require_global_chapter),
    pagination: PaginationParams = Depends(get_pagination_params),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all paragraphs for a global chapter (SUPER_ADMIN only).

    Supports pagination with `page` and `page_size` query parameters.
    """
    chapter, _ = chapter_and_textbook
    paragraph_repo = ParagraphRepository(db)
    paragraphs, total = await paragraph_repo.get_by_chapter_paginated(
        chapter_id=chapter.id,
        page=pagination.page,
        page_size=pagination.page_size,
    )
    return PaginatedResponse.create(paragraphs, total, pagination.page, pagination.page_size)


@router.get("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def get_global_paragraph(
    paragraph_data: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
):
    """
    Get a single paragraph by ID (SUPER_ADMIN only).
    Verifies that the paragraph belongs to a global textbook.
    """
    paragraph, _, _ = paragraph_data
    return paragraph


@router.put("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def update_global_paragraph(
    data: ParagraphUpdate,
    paragraph_data: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a paragraph in a global chapter (SUPER_ADMIN only).
    """
    paragraph, _, _ = paragraph_data
    paragraph_repo = ParagraphRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paragraph, field, value)

    return await paragraph_repo.update(paragraph)


@router.delete("/paragraphs/{paragraph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_paragraph(
    paragraph_data: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a paragraph in a global chapter (SUPER_ADMIN only).
    """
    paragraph, _, _ = paragraph_data
    paragraph_repo = ParagraphRepository(db)
    await paragraph_repo.soft_delete(paragraph)
