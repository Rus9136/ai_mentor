"""
Global Test CRUD endpoints for SUPER_ADMIN.
Manages global tests (school_id = NULL).
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.test import Test
from app.repositories.test_repo import TestRepository
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.schemas.test import (
    TestCreate,
    TestUpdate,
    TestResponse,
    TestListResponse,
)
from ._dependencies import require_global_test


router = APIRouter()


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_global_test(
    data: TestCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new global test (SUPER_ADMIN only).
    Global tests have school_id = NULL and are accessible to all schools.

    textbook_id is required. chapter_id and paragraph_id are optional.
    Validates hierarchical consistency (chapter belongs to textbook, paragraph belongs to chapter).
    """
    test_repo = TestRepository(db)
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)
    paragraph_repo = ParagraphRepository(db)

    # Validate textbook exists and is global
    textbook = await textbook_repo.get_by_id(data.textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {data.textbook_id} not found"
        )
    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create global test for non-global textbook"
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

    # Create test with school_id = NULL (global)
    test = Test(
        school_id=None,  # Global test
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


@router.get("/tests", response_model=List[TestListResponse])
async def list_global_tests(
    chapter_id: int = None,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all global tests (SUPER_ADMIN only).
    Optionally filter by chapter_id.
    """
    test_repo = TestRepository(db)

    if chapter_id:
        # Get tests for specific chapter (global only)
        return await test_repo.get_by_chapter(chapter_id, school_id=None)
    else:
        # Get all global tests
        return await test_repo.get_all_global()


@router.get("/tests/{test_id}", response_model=TestResponse)
async def get_global_test(
    test: Test = Depends(require_global_test),
    current_user: User = Depends(require_super_admin),
):
    """
    Get a specific global test by ID (SUPER_ADMIN only).
    """
    return test


@router.put("/tests/{test_id}", response_model=TestResponse)
async def update_global_test(
    data: TestUpdate,
    test: Test = Depends(require_global_test),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a global test (SUPER_ADMIN only).
    Validates hierarchical consistency when textbook_id, chapter_id or paragraph_id change.
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
        if textbook.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot assign global test to non-global textbook"
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


@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_test(
    test: Test = Depends(require_global_test),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a global test (SUPER_ADMIN only).
    """
    test_repo = TestRepository(db)
    await test_repo.soft_delete(test)
