"""
School Paragraph Management API for ADMIN.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.paragraph import Paragraph
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.schemas.paragraph import (
    ParagraphCreate,
    ParagraphUpdate,
    ParagraphResponse,
    ParagraphListResponse,
)
from ._dependencies import (
    get_chapter_for_school_admin,
    get_paragraph_for_school_admin,
    require_school_paragraph,
)


router = APIRouter(tags=["School Paragraphs"])


@router.post("/paragraphs", response_model=ParagraphResponse, status_code=status.HTTP_201_CREATED)
async def create_school_paragraph(
    data: ParagraphCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new paragraph in a school chapter (ADMIN only).
    Cannot add paragraphs to global chapters.
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)
    paragraph_repo = ParagraphRepository(db)

    # Verify chapter exists and belongs to school textbook
    chapter = await chapter_repo.get_by_id(data.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {data.chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook:
        if textbook.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot add paragraphs to global chapters. Contact SUPER_ADMIN."
            )

        if textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chapter"
            )

    # Create paragraph
    paragraph = Paragraph(**data.model_dump())
    return await paragraph_repo.create(paragraph)


@router.get("/chapters/{chapter_id}/paragraphs", response_model=List[ParagraphListResponse])
async def list_school_paragraphs(
    chapter_id: int,
    chapter=Depends(get_chapter_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all paragraphs for a chapter (ADMIN only).
    Works for both global and school chapters.
    """
    paragraph_repo = ParagraphRepository(db)
    return await paragraph_repo.get_by_chapter(chapter_id)


@router.get("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def get_school_paragraph(
    paragraph: Paragraph = Depends(get_paragraph_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a single paragraph from a school chapter (ADMIN only).
    Can access paragraphs from both global and school chapters.
    """
    return paragraph


@router.put("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def update_school_paragraph(
    data: ParagraphUpdate,
    paragraph_hierarchy=Depends(require_school_paragraph),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a paragraph in a school chapter (ADMIN only).
    Cannot update paragraphs in global chapters.
    """
    paragraph, chapter, textbook = paragraph_hierarchy
    paragraph_repo = ParagraphRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paragraph, field, value)

    return await paragraph_repo.update(paragraph)


@router.delete("/paragraphs/{paragraph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_paragraph(
    paragraph_hierarchy=Depends(require_school_paragraph),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a paragraph in a school chapter (ADMIN only).
    Cannot delete paragraphs in global chapters.
    """
    paragraph, chapter, textbook = paragraph_hierarchy
    paragraph_repo = ParagraphRepository(db)
    await paragraph_repo.soft_delete(paragraph)
