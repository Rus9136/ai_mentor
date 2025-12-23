"""
Global content management API for SUPER_ADMIN.
Manages global textbooks, chapters, and paragraphs (school_id = NULL).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
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
from app.repositories.goso_repo import GosoRepository, ParagraphOutcomeRepository
from app.models.goso import ParagraphOutcome, LearningOutcome
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
from app.schemas.goso import (
    ParagraphOutcomeCreate,
    ParagraphOutcomeUpdate,
    ParagraphOutcomeResponse,
    ParagraphOutcomeWithDetails,
)

router = APIRouter()


# ========== Textbook Endpoints ==========

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

    # Create textbook with school_id = NULL (global)
    textbook = Textbook(
        school_id=None,  # Global textbook
        global_textbook_id=None,
        is_customized=False,
        version=1,
        **data.model_dump()
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
    textbook_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific global textbook by ID (SUPER_ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global textbook. Use school admin endpoints."
        )

    return textbook


@router.put("/textbooks/{textbook_id}", response_model=TextbookResponse)
async def update_global_textbook(
    textbook_id: int,
    data: TextbookUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a global textbook (SUPER_ADMIN only).
    Increments version number on update.
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global textbook. Use school admin endpoints."
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(textbook, field, value)

    # Increment version on any update
    textbook.version += 1

    return await textbook_repo.update(textbook)


@router.delete("/textbooks/{textbook_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_textbook(
    textbook_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a global textbook (SUPER_ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global textbook. Use school admin endpoints."
        )

    await textbook_repo.soft_delete(textbook)


# ========== Chapter Endpoints ==========

@router.post("/chapters", response_model=ChapterResponse, status_code=status.HTTP_201_CREATED)
async def create_global_chapter(
    data: ChapterCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new chapter in a global textbook (SUPER_ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)

    # Verify textbook exists and is global
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


@router.get("/textbooks/{textbook_id}/chapters", response_model=List[ChapterListResponse])
async def list_global_chapters(
    textbook_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all chapters for a global textbook (SUPER_ADMIN only).
    """
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)

    # Verify textbook exists and is global
    textbook = await textbook_repo.get_by_id(textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global textbook. Use school admin endpoints."
        )

    return await chapter_repo.get_by_textbook(textbook_id)


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_global_chapter(
    chapter_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single chapter from a global textbook (SUPER_ADMIN only).
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Verify parent textbook is global
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a chapter in a global textbook. Use school admin endpoints."
        )

    return chapter


@router.put("/chapters/{chapter_id}", response_model=ChapterResponse)
async def update_global_chapter(
    chapter_id: int,
    data: ChapterUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a chapter in a global textbook (SUPER_ADMIN only).
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Verify parent textbook is global
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update chapter in non-global textbook. Use school admin endpoints."
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chapter, field, value)

    return await chapter_repo.update(chapter)


@router.delete("/chapters/{chapter_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_chapter(
    chapter_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a chapter in a global textbook (SUPER_ADMIN only).
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Verify parent textbook is global
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete chapter in non-global textbook. Use school admin endpoints."
        )

    await chapter_repo.soft_delete(chapter)


# ========== Paragraph Endpoints ==========

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


@router.get("/chapters/{chapter_id}/paragraphs", response_model=List[ParagraphListResponse])
async def list_global_paragraphs(
    chapter_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all paragraphs for a global chapter (SUPER_ADMIN only).
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)
    paragraph_repo = ParagraphRepository(db)

    # Verify chapter exists and belongs to global textbook
    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global chapter. Use school admin endpoints."
        )

    return await paragraph_repo.get_by_chapter(chapter_id)


@router.get("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def get_global_paragraph(
    paragraph_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single paragraph by ID (SUPER_ADMIN only).

    Verifies that the paragraph belongs to a global textbook.
    """
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    # Get paragraph
    paragraph = await paragraph_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Verify it belongs to a global textbook
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {paragraph.chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook and textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global paragraph. Use school admin endpoints."
        )

    return paragraph


@router.put("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def update_global_paragraph(
    paragraph_id: int,
    data: ParagraphUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a paragraph in a global chapter (SUPER_ADMIN only).
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

    # Verify belongs to global textbook
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook and textbook.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update paragraph in non-global chapter. Use school admin endpoints."
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(paragraph, field, value)

    return await paragraph_repo.update(paragraph)


@router.delete("/paragraphs/{paragraph_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_paragraph(
    paragraph_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a paragraph in a global chapter (SUPER_ADMIN only).
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

    # Verify belongs to global textbook
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook and textbook.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete paragraph in non-global chapter. Use school admin endpoints."
            )

    await paragraph_repo.soft_delete(paragraph)


# ========== Test Endpoints ==========

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
    test_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific global test by ID (SUPER_ADMIN only).
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global test. Use school admin endpoints."
        )

    return test


@router.put("/tests/{test_id}", response_model=TestResponse)
async def update_global_test(
    test_id: int,
    data: TestUpdate,
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

    test = await test_repo.get_by_id(test_id)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global test. Use school admin endpoints."
        )

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
    test_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a global test (SUPER_ADMIN only).
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global test. Use school admin endpoints."
        )

    await test_repo.soft_delete(test)


# ========== Question Endpoints ==========

@router.post("/tests/{test_id}/questions", status_code=status.HTTP_201_CREATED)
async def create_global_question(
    test_id: int,
    data: QuestionCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new question in a global test (SUPER_ADMIN only).
    Supports creating question with nested options in a single request.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    # Verify test exists and is global
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add question to non-global test. Use school admin endpoints."
        )

    # Extract options from data (will be created separately)
    options_data = data.options
    question_data = data.model_dump(exclude={'options'})

    # Create question
    question = Question(test_id=test_id, **question_data)
    created_question = await question_repo.create(question)

    # Create options if provided
    created_options = []
    if options_data:
        for option_create in options_data:
            option = QuestionOption(
                question_id=created_question.id,
                **option_create.model_dump()
            )
            created_option = await option_repo.create(option)
            created_options.append(created_option)

    # Return question details as simple dict (avoid SQLAlchemy lazy loading)
    return {
        "id": created_question.id,
        "test_id": created_question.test_id,
        "sort_order": created_question.sort_order,
        "question_type": created_question.question_type.value if hasattr(created_question.question_type, 'value') else created_question.question_type,
        "question_text": created_question.question_text,
        "explanation": created_question.explanation,
        "points": created_question.points,
        "created_at": created_question.created_at.isoformat() if created_question.created_at else None,
        "updated_at": created_question.updated_at.isoformat() if created_question.updated_at else None,
        "deleted_at": created_question.deleted_at.isoformat() if created_question.deleted_at else None,
        "is_deleted": created_question.is_deleted,
        "options": [
            {
                "id": opt.id,
                "question_id": opt.question_id,
                "sort_order": opt.sort_order,
                "option_text": opt.option_text,
                "is_correct": opt.is_correct,
                "created_at": opt.created_at.isoformat() if opt.created_at else None,
                "updated_at": opt.updated_at.isoformat() if opt.updated_at else None,
                "deleted_at": opt.deleted_at.isoformat() if opt.deleted_at else None,
                "is_deleted": opt.is_deleted,
            }
            for opt in created_options
        ]
    }


@router.get("/tests/{test_id}/questions", response_model=List[QuestionResponse])
async def list_global_questions(
    test_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all questions for a global test (SUPER_ADMIN only).

    Returns questions with options loaded manually in the same session
    to avoid RLS session variable issues with eager loading.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    # Verify test exists and is global
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global test. Use school admin endpoints."
        )

    # Get questions WITHOUT eager loading options (avoid RLS issues)
    questions = await question_repo.get_by_test(test_id, load_options=False)

    # Manually load options and build response (avoid SQLAlchemy lazy load issues)
    result = []
    for question in questions:
        options = await option_repo.get_by_question(question.id)

        # Build Pydantic models from dict to avoid accessing SQLAlchemy relationships
        q_dict = {
            "id": question.id,
            "test_id": question.test_id,
            "sort_order": question.sort_order,
            "question_type": question.question_type,
            "question_text": question.question_text,
            "explanation": question.explanation,
            "points": question.points,
            "created_at": question.created_at,
            "updated_at": question.updated_at,
            "deleted_at": question.deleted_at,
            "is_deleted": question.is_deleted,
            "options": [
                {
                    "id": opt.id,
                    "question_id": opt.question_id,
                    "sort_order": opt.sort_order,
                    "option_text": opt.option_text,
                    "is_correct": opt.is_correct,
                    "created_at": opt.created_at,
                    "updated_at": opt.updated_at,
                    "deleted_at": opt.deleted_at,
                    "is_deleted": opt.is_deleted,
                }
                for opt in options
            ]
        }
        q_response = QuestionResponse(**q_dict)
        result.append(q_response)

    return result


@router.get("/questions/{question_id}", response_model=QuestionResponse)
async def get_global_question(
    question_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific question by ID (SUPER_ADMIN only).
    """
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test is global
    test = await test_repo.get_by_id(question.test_id)
    if test and test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This question belongs to a non-global test. Use school admin endpoints."
        )

    return question


@router.put("/questions/{question_id}")
async def update_global_question(
    question_id: int,
    data: QuestionUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question in a global test (SUPER_ADMIN only).
    Returns question with options loaded manually to avoid RLS session variable issues.
    """
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)
    test_repo = TestRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test is global
    test = await test_repo.get_by_id(question.test_id)
    if test and test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot update question in non-global test. Use school admin endpoints."
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    updated_question = await question_repo.update(question)

    # Manually load options (avoid SQLAlchemy lazy loading issues)
    options = await option_repo.get_by_question(updated_question.id)

    # Return question details as simple dict (avoid SQLAlchemy lazy loading)
    return {
        "id": updated_question.id,
        "test_id": updated_question.test_id,
        "sort_order": updated_question.sort_order,
        "question_type": updated_question.question_type.value if hasattr(updated_question.question_type, 'value') else updated_question.question_type,
        "question_text": updated_question.question_text,
        "explanation": updated_question.explanation,
        "points": updated_question.points,
        "created_at": updated_question.created_at.isoformat() if updated_question.created_at else None,
        "updated_at": updated_question.updated_at.isoformat() if updated_question.updated_at else None,
        "deleted_at": updated_question.deleted_at.isoformat() if updated_question.deleted_at else None,
        "is_deleted": updated_question.is_deleted,
        "options": [
            {
                "id": opt.id,
                "question_id": opt.question_id,
                "sort_order": opt.sort_order,
                "option_text": opt.option_text,
                "is_correct": opt.is_correct,
                "created_at": opt.created_at.isoformat() if opt.created_at else None,
                "updated_at": opt.updated_at.isoformat() if opt.updated_at else None,
                "deleted_at": opt.deleted_at.isoformat() if opt.deleted_at else None,
                "is_deleted": opt.is_deleted,
            }
            for opt in options
        ]
    }


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_question(
    question_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question in a global test (SUPER_ADMIN only).
    """
    question_repo = QuestionRepository(db)
    test_repo = TestRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    # Verify parent test is global
    test = await test_repo.get_by_id(question.test_id)
    if test and test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete question in non-global test. Use school admin endpoints."
        )

    await question_repo.soft_delete(question)


# ========== QuestionOption Endpoints ==========

@router.post("/questions/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_global_question_option(
    question_id: int,
    data: QuestionOptionCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new option for a question in a global test (SUPER_ADMIN only).
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

    # Verify parent test is global
    test = await test_repo.get_by_id(question.test_id)
    if test and test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot add option to question in non-global test. Use school admin endpoints."
        )

    # Create option
    option = QuestionOption(question_id=question_id, **data.model_dump())
    return await option_repo.create(option)


@router.put("/options/{option_id}")
async def update_global_question_option(
    option_id: int,
    data: QuestionOptionUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question option in a global test (SUPER_ADMIN only).
    Returns option as dict to avoid SQLAlchemy lazy loading issues.
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

    # Verify parent question's test is global
    question = await question_repo.get_by_id(option.question_id)
    if question:
        test = await test_repo.get_by_id(question.test_id)
        if test and test.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot update option in non-global test. Use school admin endpoints."
            )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)

    updated_option = await option_repo.update(option)

    # Return option as simple dict (avoid SQLAlchemy lazy loading issues)
    return {
        "id": updated_option.id,
        "question_id": updated_option.question_id,
        "sort_order": updated_option.sort_order,
        "option_text": updated_option.option_text,
        "is_correct": updated_option.is_correct,
        "created_at": updated_option.created_at.isoformat() if updated_option.created_at else None,
        "updated_at": updated_option.updated_at.isoformat() if updated_option.updated_at else None,
        "deleted_at": updated_option.deleted_at.isoformat() if updated_option.deleted_at else None,
        "is_deleted": updated_option.is_deleted,
    }


@router.delete("/options/{option_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_question_option(
    option_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a question option in a global test (SUPER_ADMIN only).
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

    # Verify parent question's test is global
    question = await question_repo.get_by_id(option.question_id)
    if question:
        test = await test_repo.get_by_id(question.test_id)
        if test and test.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot delete option in non-global test. Use school admin endpoints."
            )

    await option_repo.soft_delete(option)


# ========== Paragraph Outcomes Endpoints (GOSO mapping) ==========

@router.post("/paragraph-outcomes", response_model=ParagraphOutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_global_paragraph_outcome(
    data: ParagraphOutcomeCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a paragraph-outcome link for a global paragraph (SUPER_ADMIN only).

    Links a global paragraph (school_id = NULL) to a learning outcome from GOSO.
    This mapping indicates which learning objectives are covered by the paragraph.
    """
    paragraph_repo = ParagraphRepository(db)
    goso_repo = GosoRepository(db)
    po_repo = ParagraphOutcomeRepository(db)

    # 1. Check paragraph exists
    paragraph = await paragraph_repo.get_by_id(data.paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {data.paragraph_id} not found"
        )

    # 2. Verify paragraph is global (school_id = NULL)
    # Need to check via chapter -> textbook
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {paragraph.chapter_id} not found"
        )

    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {chapter.textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create mapping for non-global paragraph. Use school admin endpoints."
        )

    # 3. Check outcome exists and is active
    outcome = await goso_repo.get_outcome_by_id(data.outcome_id)
    if not outcome:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning outcome {data.outcome_id} not found"
        )

    if not outcome.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Learning outcome {data.outcome_id} is inactive"
        )

    # 4. Check for duplicate
    existing = await po_repo.get_by_paragraph_and_outcome(
        data.paragraph_id, data.outcome_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mapping already exists between paragraph {data.paragraph_id} and outcome {data.outcome_id}"
        )

    # 5. Create the link
    paragraph_outcome = ParagraphOutcome(
        paragraph_id=data.paragraph_id,
        outcome_id=data.outcome_id,
        confidence=data.confidence,
        anchor=data.anchor,
        notes=data.notes,
        created_by=current_user.id,
    )

    created = await po_repo.create(paragraph_outcome)
    return created


@router.get("/paragraphs/{paragraph_id}/outcomes", response_model=list[ParagraphOutcomeWithDetails])
async def get_global_paragraph_outcomes(
    paragraph_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all outcomes linked to a global paragraph (SUPER_ADMIN only).

    Returns all learning outcomes mapped to the specified paragraph.
    """
    paragraph_repo = ParagraphRepository(db)
    po_repo = ParagraphOutcomeRepository(db)

    # Check paragraph exists
    paragraph = await paragraph_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Get links with outcome details
    links = await po_repo.get_by_paragraph(paragraph_id, load_outcome=True)

    # Build response
    result = []
    for link in links:
        response_data = {
            "id": link.id,
            "paragraph_id": link.paragraph_id,
            "outcome_id": link.outcome_id,
            "confidence": link.confidence,
            "anchor": link.anchor,
            "notes": link.notes,
            "created_by": link.created_by,
            "created_at": link.created_at,
            "outcome_code": None,
            "outcome_title_ru": None,
            "outcome_grade": None,
        }

        if link.outcome:
            response_data["outcome_code"] = link.outcome.code
            response_data["outcome_title_ru"] = link.outcome.title_ru
            response_data["outcome_grade"] = link.outcome.grade

        result.append(ParagraphOutcomeWithDetails(**response_data))

    return result


@router.put("/paragraph-outcomes/{outcome_link_id}", response_model=ParagraphOutcomeResponse)
async def update_global_paragraph_outcome(
    outcome_link_id: int,
    data: ParagraphOutcomeUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a paragraph-outcome link (SUPER_ADMIN only).

    Updates the confidence, anchor, or notes of an existing mapping.
    """
    po_repo = ParagraphOutcomeRepository(db)

    # Get existing link
    link = await po_repo.get_by_id(outcome_link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph-outcome link {outcome_link_id} not found"
        )

    # Update fields
    if data.confidence is not None:
        link.confidence = data.confidence
    if data.anchor is not None:
        link.anchor = data.anchor
    if data.notes is not None:
        link.notes = data.notes

    updated = await po_repo.update(link)
    return updated


@router.delete("/paragraph-outcomes/{outcome_link_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_global_paragraph_outcome(
    outcome_link_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a paragraph-outcome link (SUPER_ADMIN only).

    Permanently removes the mapping between a paragraph and learning outcome.
    This is a hard delete, not a soft delete.
    """
    po_repo = ParagraphOutcomeRepository(db)

    # Get existing link
    link = await po_repo.get_by_id(outcome_link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph-outcome link {outcome_link_id} not found"
        )

    await po_repo.delete(link)
