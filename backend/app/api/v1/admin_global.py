"""
Global content management API for SUPER_ADMIN.
Manages global textbooks, chapters, and paragraphs (school_id = NULL).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
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
    """
    test_repo = TestRepository(db)
    chapter_repo = ChapterRepository(db)

    # If chapter_id is provided, verify it's a global chapter
    if data.chapter_id:
        chapter = await chapter_repo.get_by_id(data.chapter_id)
        if not chapter:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Chapter {data.chapter_id} not found"
            )

        # Verify chapter belongs to global textbook
        textbook_repo = TextbookRepository(db)
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook and textbook.school_id is not None:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot create global test for non-global chapter"
            )

    # Create test with school_id = NULL (global)
    # Pass fields directly to preserve enum objects
    test = Test(
        school_id=None,  # Global test
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
    test = await test_repo.get_by_id(test_id, load_questions=True)

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

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
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

@router.post("/tests/{test_id}/questions", response_model=QuestionResponse, status_code=status.HTTP_201_CREATED)
async def create_global_question(
    test_id: int,
    data: QuestionCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new question in a global test (SUPER_ADMIN only).
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)

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

    # Create question
    question = Question(test_id=test_id, **data.model_dump())
    return await question_repo.create(question)


@router.get("/tests/{test_id}/questions", response_model=List[QuestionResponse])
async def list_global_questions(
    test_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all questions for a global test (SUPER_ADMIN only).
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)

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

    return await question_repo.get_by_test(test_id)


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


@router.put("/questions/{question_id}", response_model=QuestionResponse)
async def update_global_question(
    question_id: int,
    data: QuestionUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question in a global test (SUPER_ADMIN only).
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
            detail="Cannot update question in non-global test. Use school admin endpoints."
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    return await question_repo.update(question)


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


@router.put("/options/{option_id}", response_model=QuestionOptionResponse)
async def update_global_question_option(
    option_id: int,
    data: QuestionOptionUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a question option in a global test (SUPER_ADMIN only).
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

    return await option_repo.update(option)


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
