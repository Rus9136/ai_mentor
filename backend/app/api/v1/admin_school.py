"""
School content management API for ADMIN.
Manages school-specific textbooks, chapters, paragraphs, and customization (fork).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.schemas.textbook import (
    TextbookCreate,
    TextbookUpdate,
    TextbookResponse,
    TextbookListResponse,
)
from app.schemas.chapter import (
    ChapterCreate,
    ChapterUpdate,
    ChapterResponse,
    ChapterListResponse,
)
from app.schemas.paragraph import (
    ParagraphCreate,
    ParagraphUpdate,
    ParagraphResponse,
    ParagraphListResponse,
)
from app.schemas.test import (
    TestCreate,
    TestUpdate,
    TestResponse,
    TestListResponse,
)
from app.schemas.question import (
    QuestionCreate,
    QuestionUpdate,
    QuestionResponse,
    QuestionListResponse,
    QuestionOptionCreate,
    QuestionOptionUpdate,
    QuestionOptionResponse,
)

router = APIRouter()


# ========== Textbook Endpoints ==========

@router.get("/textbooks", response_model=List[TextbookListResponse])
async def list_school_textbooks(
    include_global: bool = True,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get textbooks for the school (ADMIN only).
    By default, includes both school-specific and global textbooks.
    """
    textbook_repo = TextbookRepository(db)
    return await textbook_repo.get_by_school(school_id, include_global=include_global)


@router.post("/textbooks", response_model=TextbookResponse, status_code=status.HTTP_201_CREATED)
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

    # Create textbook with current school_id
    textbook = Textbook(
        school_id=school_id,  # School-specific textbook
        global_textbook_id=None,
        is_customized=False,
        version=1,
        **data.model_dump()
    )

    return await textbook_repo.create(textbook)


@router.post("/textbooks/{global_textbook_id}/customize", response_model=TextbookResponse, status_code=status.HTTP_201_CREATED)
async def customize_global_textbook(
    global_textbook_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Customize (fork) a global textbook for the school (ADMIN only).
    Creates a complete copy with all chapters and paragraphs.
    The copy has is_customized=True and references the original via global_textbook_id.
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


@router.get("/textbooks/{textbook_id}", response_model=TextbookResponse)
async def get_school_textbook(
    textbook_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific textbook accessible to the school (ADMIN only).
    Can view both global and school-specific textbooks.
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    # Allow if global OR belongs to school
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    return textbook


@router.put("/textbooks/{textbook_id}", response_model=TextbookResponse)
async def update_school_textbook(
    textbook_id: int,
    data: TextbookUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a school-specific textbook (ADMIN only).
    Cannot update global textbooks.
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update global textbooks. Contact SUPER_ADMIN."
        )

    if textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(textbook, field, value)

    # Increment version on update
    textbook.version += 1

    return await textbook_repo.update(textbook)


@router.delete("/textbooks/{textbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_textbook(
    textbook_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a school-specific textbook (ADMIN only).
    Cannot delete global textbooks.
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete global textbooks. Contact SUPER_ADMIN."
        )

    if textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    await textbook_repo.soft_delete(textbook)


# ========== Chapter Endpoints ==========

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
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chapters for a textbook (ADMIN only).
    Works for both global and school textbooks.
    """
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)

    # Verify textbook exists and is accessible
    textbook = await textbook_repo.get_by_id(textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    return await chapter_repo.get_by_textbook(textbook_id)


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_school_chapter(
    chapter_id: int,
    data: ChapterUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a chapter in a school textbook (ADMIN only).
    Cannot update chapters in global textbooks.
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Verify parent textbook belongs to school
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook:
        if textbook.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update chapters in global textbooks. Contact SUPER_ADMIN."
            )

        if textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chapter"
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chapter, field, value)

    return await chapter_repo.update(chapter)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_chapter(
    chapter_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a chapter in a school textbook (ADMIN only).
    Cannot delete chapters in global textbooks.
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Verify parent textbook belongs to school
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook:
        if textbook.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete chapters in global textbooks. Contact SUPER_ADMIN."
            )

        if textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chapter"
            )

    await chapter_repo.soft_delete(chapter)


# ========== Paragraph Endpoints ==========

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
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all paragraphs for a chapter (ADMIN only).
    Works for both global and school chapters.
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)
    paragraph_repo = ParagraphRepository(db)

    # Verify chapter exists and is accessible
    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    return await paragraph_repo.get_by_chapter(chapter_id)


@router.put("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def update_school_paragraph(
    paragraph_id: int,
    data: ParagraphUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a paragraph in a school chapter (ADMIN only).
    Cannot update paragraphs in global chapters.
    """
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    paragraph = await paragraph_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Verify belongs to school textbook
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook:
            if textbook.school_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot update paragraphs in global chapters. Contact SUPER_ADMIN."
                )

            if textbook.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this paragraph"
                )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paragraph, field, value)

    return await paragraph_repo.update(paragraph)


@router.delete("/paragraphs/{paragraph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_paragraph(
    paragraph_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a paragraph in a school chapter (ADMIN only).
    Cannot delete paragraphs in global chapters.
    """
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    paragraph = await paragraph_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Verify belongs to school textbook
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook:
            if textbook.school_id is None:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete paragraphs in global chapters. Contact SUPER_ADMIN."
                )

            if textbook.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this paragraph"
                )

    await paragraph_repo.soft_delete(paragraph)


# ========== Test Endpoints ==========

@router.get("/tests", response_model=List[TestListResponse])
async def list_school_tests(
    include_global: bool = True,
    chapter_id: int = None,
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
        # Get tests for specific chapter (school + global if requested)
        if include_global:
            return await test_repo.get_by_chapter(chapter_id, school_id=school_id)
        else:
            # Only school tests for this chapter
            tests = await test_repo.get_by_chapter(chapter_id, school_id=school_id)
            return [t for t in tests if t.school_id == school_id]
    else:
        # Get all tests
        return await test_repo.get_by_school(school_id, include_global=include_global)


@router.post("/tests", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_school_test(
    data: TestCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new school-specific test (ADMIN only).
    """
    test_repo = TestRepository(db)

    # Verify chapter belongs to school (if chapter_id provided)
    if data.chapter_id:
        chapter_repo = ChapterRepository(db)
        textbook_repo = TextbookRepository(db)

        chapter = await chapter_repo.get_by_id(data.chapter_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {data.chapter_id} not found"
            )

        # Verify chapter belongs to school or is global
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook and textbook.school_id is not None and textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create test for chapter from another school"
            )

    # Create test with current school_id
    # Pass fields directly to preserve enum objects
    test = Test(
        school_id=school_id,  # School-specific test
        title=data.title,
        description=data.description,
        chapter_id=data.chapter_id,
        paragraph_id=data.paragraph_id,
        difficulty=data.difficulty,  # Enum object
        time_limit=data.time_limit,
        passing_score=data.passing_score,
        is_active=data.is_active,
    )

    return await test_repo.create(test)


@router.get("/tests/{test_id}", response_model=TestResponse)
async def get_school_test(
    test_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific test by ID (ADMIN only).
    Can access both global and own school tests.
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id, load_questions=True)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    # Verify access: must be global or belong to this school
    if test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    return test


@router.put("/tests/{test_id}", response_model=TestResponse)
async def update_school_test(
    test_id: int,
    data: TestUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a school-specific test (ADMIN only).
    Cannot update global tests.
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    # Cannot modify global tests
    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update global tests. Contact SUPER_ADMIN."
        )

    # Verify ownership
    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(test, field, value)

    return await test_repo.update(test)


@router.delete("/tests/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_test(
    test_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a school-specific test (ADMIN only).
    Cannot delete global tests.
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    # Cannot delete global tests
    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete global tests. Contact SUPER_ADMIN."
        )

    # Verify ownership
    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    await test_repo.soft_delete(test)


# ========== Question Endpoints ==========

@router.post("/tests/{test_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_school_question(
    test_id: int,
    data: QuestionCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new question in a school test (ADMIN only).
    Cannot add questions to global tests.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)

    # Verify test exists
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    # Cannot add questions to global tests
    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add questions to global tests. Contact SUPER_ADMIN."
        )

    # Verify ownership
    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    # Create question
    question = Question(test_id=test_id, **data.model_dump())
    return await question_repo.create(question)


@router.get("/tests/{test_id}/questions", response_model=List[QuestionResponse])
async def list_school_questions(
    test_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all questions for a test (ADMIN only).
    Can access questions from global and own school tests.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)

    # Verify test exists
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    # Verify access: must be global or belong to this school
    if test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    return await question_repo.get_by_test(test_id)


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_school_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific question by ID (ADMIN only).
    Can access questions from global and own school tests.
    """
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test access
    test = await test_repo.get_by_id(question.test_id)
    if test and test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this question"
        )

    return question


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_school_question(
    question_id: int,
    data: QuestionUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question in a school test (ADMIN only).
    Cannot update questions in global tests.
    """
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test
    test = await test_repo.get_by_id(question.test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent test not found"
        )

    # Cannot modify global tests
    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update questions in global tests. Contact SUPER_ADMIN."
        )

    # Verify ownership
    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this question"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    return await question_repo.update(question)


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_question(
    question_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question in a school test (ADMIN only).
    Cannot delete questions in global tests.
    """
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test
    test = await test_repo.get_by_id(question.test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent test not found"
        )

    # Cannot delete from global tests
    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete questions in global tests. Contact SUPER_ADMIN."
        )

    # Verify ownership
    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this question"
        )

    await question_repo.soft_delete(question)


# ========== QuestionOption Endpoints ==========

@router.post("/questions/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_school_question_option(
    question_id: int,
    data: QuestionOptionCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new option for a question in a school test (ADMIN only).
    Cannot add options to questions in global tests.
    """
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    test_repo = TestRepository(db)

    # Verify question exists
    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test
    test = await test_repo.get_by_id(question.test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent test not found"
        )

    # Cannot modify global tests
    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add options to questions in global tests. Contact SUPER_ADMIN."
        )

    # Verify ownership
    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this question"
        )

    # Create option
    option = QuestionOption(question_id=question_id, **data.model_dump())
    return await option_repo.create(option)


@router.put("/options/{option_id}", response_model=QuestionOptionResponse)
async def update_school_question_option(
    option_id: int,
    data: QuestionOptionUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question option in a school test (ADMIN only).
    Cannot update options in global tests.
    """
    option_repo = QuestionOptionRepository(db)
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    option = await option_repo.get_by_id(option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QuestionOption {option_id} not found"
        )

    # Verify parent question's test
    question = await question_repo.get_by_id(option.question_id)
    if question:
        test = await test_repo.get_by_id(question.test_id)
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent test not found"
            )

        # Cannot modify global tests
        if test.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update options in global tests. Contact SUPER_ADMIN."
            )

        # Verify ownership
        if test.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this option"
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)

    return await option_repo.update(option)


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_question_option(
    option_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question option in a school test (ADMIN only).
    Cannot delete options in global tests.
    """
    option_repo = QuestionOptionRepository(db)
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    option = await option_repo.get_by_id(option_id)
    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QuestionOption {option_id} not found"
        )

    # Verify parent question's test
    question = await question_repo.get_by_id(option.question_id)
    if question:
        test = await test_repo.get_by_id(question.test_id)
        if not test:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Parent test not found"
            )

        # Cannot delete from global tests
        if test.school_id is None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete options in global tests. Contact SUPER_ADMIN."
            )

        # Verify ownership
        if test.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this option"
            )

    await option_repo.soft_delete(option)
