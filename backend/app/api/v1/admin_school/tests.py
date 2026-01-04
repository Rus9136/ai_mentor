"""
School Test Management API for ADMIN.
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.test import Test
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.test_repo import TestRepository
from app.schemas.test import (
    TestCreate,
    TestUpdate,
    TestResponse,
    TestListResponse,
)
from ._dependencies import get_test_for_school_admin, require_school_test


router = APIRouter(prefix="/tests", tags=["School Tests"])


@router.get("", response_model=List[TestListResponse])
async def list_school_tests(
    include_global: bool = True,
    chapter_id: Optional[int] = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get tests for the school (ADMIN only).
    By default, includes both school-specific and global tests.
    Optionally filter by chapter_id.
    """
    test_repo = TestRepository(db)

    if chapter_id:
        if include_global:
            return await test_repo.get_by_chapter(chapter_id, school_id=school_id)
        else:
            tests = await test_repo.get_by_chapter(chapter_id, school_id=school_id)
            return [t for t in tests if t.school_id == school_id]
    else:
        return await test_repo.get_by_school(school_id, include_global=include_global)


@router.post("", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_school_test(
    data: TestCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new school-specific test (ADMIN only).
    textbook_id is required. chapter_id and paragraph_id are optional.
    Validates hierarchical consistency and school ownership.
    """
    test_repo = TestRepository(db)
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)
    paragraph_repo = ParagraphRepository(db)

    # Validate textbook exists and belongs to school or is global
    textbook = await textbook_repo.get_by_id(data.textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {data.textbook_id} not found"
        )
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create test for textbook from another school"
        )

    # If chapter_id is provided, verify it belongs to the textbook
    if data.chapter_id:
        chapter = await chapter_repo.get_by_id(data.chapter_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {data.chapter_id} not found"
            )
        if chapter.textbook_id != data.textbook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chapter {data.chapter_id} does not belong to textbook {data.textbook_id}"
            )

    # If paragraph_id is provided, verify it belongs to the chapter
    if data.paragraph_id:
        if not data.chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="paragraph_id requires chapter_id to be set"
            )
        paragraph = await paragraph_repo.get_by_id(data.paragraph_id)
        if not paragraph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paragraph {data.paragraph_id} not found"
            )
        if paragraph.chapter_id != data.chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paragraph {data.paragraph_id} does not belong to chapter {data.chapter_id}"
            )

    # Create test with current school_id
    test = Test(
        school_id=school_id,
        textbook_id=data.textbook_id,
        title=data.title,
        description=data.description,
        chapter_id=data.chapter_id,
        paragraph_id=data.paragraph_id,
        difficulty=data.difficulty,
        time_limit=data.time_limit,
        passing_score=data.passing_score,
        is_active=data.is_active,
    )

    return await test_repo.create(test)


@router.get("/{test_id}", response_model=TestResponse)
async def get_school_test(
    test: Test = Depends(get_test_for_school_admin),
    current_user: User = Depends(require_admin),
):
    """
    Get a specific test by ID (ADMIN only).
    Can access both global and own school tests.
    """
    return test


@router.put("/{test_id}", response_model=TestResponse)
async def update_school_test(
    data: TestUpdate,
    test: Test = Depends(require_school_test),
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a school-specific test (ADMIN only).
    Cannot update global tests. Validates hierarchical consistency.
    """
    test_repo = TestRepository(db)
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)
    paragraph_repo = ParagraphRepository(db)

    update_data = data.model_dump(exclude_unset=True)

    # Determine effective values after update
    new_textbook_id = update_data.get('textbook_id', test.textbook_id)
    new_chapter_id = update_data.get('chapter_id', test.chapter_id)
    new_paragraph_id = update_data.get('paragraph_id', test.paragraph_id)

    # Validate textbook if it's being changed
    if 'textbook_id' in update_data and update_data['textbook_id'] is not None:
        textbook = await textbook_repo.get_by_id(update_data['textbook_id'])
        if not textbook:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Textbook {update_data['textbook_id']} not found"
            )
        if textbook.school_id is not None and textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign test to textbook from another school"
            )

    # Validate chapter belongs to textbook
    if new_chapter_id:
        chapter = await chapter_repo.get_by_id(new_chapter_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {new_chapter_id} not found"
            )
        if new_textbook_id and chapter.textbook_id != new_textbook_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Chapter {new_chapter_id} does not belong to textbook {new_textbook_id}"
            )

    # Validate paragraph belongs to chapter
    if new_paragraph_id:
        if not new_chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="paragraph_id requires chapter_id to be set"
            )
        paragraph = await paragraph_repo.get_by_id(new_paragraph_id)
        if not paragraph:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Paragraph {new_paragraph_id} not found"
            )
        if paragraph.chapter_id != new_chapter_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Paragraph {new_paragraph_id} does not belong to chapter {new_chapter_id}"
            )

    # Update fields
    for field, value in update_data.items():
        setattr(test, field, value)

    return await test_repo.update(test)


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_test(
    test: Test = Depends(require_school_test),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a school-specific test (ADMIN only).
    Cannot delete global tests.
    """
    test_repo = TestRepository(db)
    await test_repo.soft_delete(test)
