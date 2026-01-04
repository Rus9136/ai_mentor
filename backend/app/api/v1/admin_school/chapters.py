"""
School Chapter Management API for ADMIN.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.chapter import Chapter
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterListResponse,
)
from ._dependencies import (
    get_textbook_for_school_admin,
    require_school_textbook,
    get_chapter_for_school_admin,
    require_school_chapter,
)


router = APIRouter(tags=["School Chapters"])


@router.post("/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_school_chapter(
    data: ChapterCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chapter in a school textbook (ADMIN only).
    Cannot add chapters to global textbooks.
    """
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)

    # Verify textbook exists and belongs to school
    textbook = await textbook_repo.get_by_id(data.textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {data.textbook_id} not found"
        )

    if textbook.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add chapters to global textbooks. Contact SUPER_ADMIN."
        )

    if textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    # Create chapter
    chapter = Chapter(**data.model_dump())
    return await chapter_repo.create(chapter)


@router.get("/textbooks/{textbook_id}/chapters", response_model=List[ChapterListResponse])
async def list_school_chapters(
    textbook_id: int,
    textbook=Depends(get_textbook_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chapters for a textbook (ADMIN only).
    Works for both global and school textbooks.
    """
    chapter_repo = ChapterRepository(db)
    return await chapter_repo.get_by_textbook(textbook_id)


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_school_chapter(
    chapter: Chapter = Depends(get_chapter_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a single chapter from a school textbook (ADMIN only).
    Can access chapters from both global and school textbooks.
    """
    return chapter


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_school_chapter(
    data: ChapterUpdate,
    chapter_and_textbook=Depends(require_school_chapter),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a chapter in a school textbook (ADMIN only).
    Cannot update chapters in global textbooks.
    """
    chapter, textbook = chapter_and_textbook
    chapter_repo = ChapterRepository(db)

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chapter, field, value)

    return await chapter_repo.update(chapter)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_chapter(
    chapter_and_textbook=Depends(require_school_chapter),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a chapter in a school textbook (ADMIN only).
    Cannot delete chapters in global textbooks.
    """
    chapter, textbook = chapter_and_textbook
    chapter_repo = ChapterRepository(db)
    await chapter_repo.soft_delete(chapter)
