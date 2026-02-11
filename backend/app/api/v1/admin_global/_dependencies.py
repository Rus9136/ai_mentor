"""
Reusable dependencies for Global Admin API.

These dependencies encapsulate common access checks for SUPER_ADMIN endpoints
managing global content (school_id = NULL). Each dependency handles:
1. Entity existence check (404 if not found)
2. Global content verification (403 if not global, i.e. school_id != NULL)
"""

from typing import Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption
from app.models.embedded_question import EmbeddedQuestion


# =============================================================================
# Content Access Dependencies (Textbook -> Chapter -> Paragraph hierarchy)
# =============================================================================

async def require_global_textbook(
    textbook_id: int,
    db: AsyncSession = Depends(get_db)
) -> Textbook:
    """
    Get global textbook by ID.
    Raises 404 if not found, 403 if not global (school_id != NULL).
    """
    from app.repositories.textbook_repo import TextbookRepository
    repo = TextbookRepository(db)
    textbook = await repo.get_by_id(textbook_id)

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


async def require_global_chapter(
    chapter_id: int,
    db: AsyncSession = Depends(get_db)
) -> Tuple[Chapter, Textbook]:
    """
    Get chapter in a global textbook.
    Returns tuple (chapter, textbook).
    Raises 404 if not found, 403 if parent textbook is not global.
    """
    from app.repositories.chapter_repo import ChapterRepository
    from app.repositories.textbook_repo import TextbookRepository

    chapter_repo = ChapterRepository(db)
    chapter = await chapter_repo.get_by_id(chapter_id)

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {chapter.textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a chapter in a global textbook. Use school admin endpoints."
        )

    return chapter, textbook


async def require_global_paragraph(
    paragraph_id: int,
    db: AsyncSession = Depends(get_db)
) -> Tuple[Paragraph, Chapter, Textbook]:
    """
    Get paragraph in a global textbook.
    Returns tuple (paragraph, chapter, textbook).
    Raises 404 if not found, 403 if parent textbook is not global.
    """
    from app.repositories.paragraph_repo import ParagraphRepository
    from app.repositories.chapter_repo import ChapterRepository
    from app.repositories.textbook_repo import TextbookRepository

    paragraph_repo = ParagraphRepository(db)
    paragraph = await paragraph_repo.get_by_id(paragraph_id)

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    chapter_repo = ChapterRepository(db)
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {paragraph.chapter_id} not found"
        )

    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {chapter.textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This is not a global paragraph. Use school admin endpoints."
        )

    return paragraph, chapter, textbook


# =============================================================================
# Test Access Dependencies (Test -> Question -> Option hierarchy)
# =============================================================================

async def require_global_test(
    test_id: int,
    db: AsyncSession = Depends(get_db)
) -> Test:
    """
    Get global test by ID.
    Raises 404 if not found, 403 if not global (school_id != NULL).
    """
    from app.repositories.test_repo import TestRepository
    repo = TestRepository(db)
    test = await repo.get_by_id(test_id, load_questions=False)

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


async def require_global_question(
    question_id: int,
    db: AsyncSession = Depends(get_db)
) -> Tuple[Question, Test]:
    """
    Get question in a global test.
    Returns tuple (question, test).
    Raises 404 if not found, 403 if parent test is not global.
    """
    from app.repositories.question_repo import QuestionRepository
    from app.repositories.test_repo import TestRepository

    question_repo = QuestionRepository(db)
    question = await question_repo.get_by_id(question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found"
        )

    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(question.test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {question.test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This question belongs to a non-global test. Use school admin endpoints."
        )

    return question, test


async def require_global_option(
    option_id: int,
    db: AsyncSession = Depends(get_db)
) -> Tuple[QuestionOption, Question, Test]:
    """
    Get question option in a global test.
    Returns tuple (option, question, test).
    Raises 404 if not found, 403 if parent test is not global.
    """
    from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
    from app.repositories.test_repo import TestRepository

    option_repo = QuestionOptionRepository(db)
    option = await option_repo.get_by_id(option_id)

    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"QuestionOption {option_id} not found"
        )

    question_repo = QuestionRepository(db)
    question = await question_repo.get_by_id(option.question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {option.question_id} not found"
        )

    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(question.test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {question.test_id} not found"
        )

    if test.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This option belongs to a non-global test. Use school admin endpoints."
        )

    return option, question, test


# =============================================================================
# Embedded Question Access Dependencies
# =============================================================================

async def require_global_embedded_question(
    embedded_question_id: int,
    db: AsyncSession = Depends(get_db)
) -> Tuple[EmbeddedQuestion, Paragraph, Chapter, Textbook]:
    """
    Get embedded question in a global textbook.
    Traverses: EmbeddedQuestion → Paragraph → Chapter → Textbook.
    Returns tuple (embedded_question, paragraph, chapter, textbook).
    Raises 404 if not found, 403 if parent textbook is not global.
    """
    from app.repositories.embedded_question_repo import EmbeddedQuestionRepository
    from app.repositories.paragraph_repo import ParagraphRepository
    from app.repositories.chapter_repo import ChapterRepository
    from app.repositories.textbook_repo import TextbookRepository

    eq_repo = EmbeddedQuestionRepository(db)
    question = await eq_repo.get_by_id(embedded_question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Embedded question {embedded_question_id} not found"
        )

    paragraph_repo = ParagraphRepository(db)
    paragraph = await paragraph_repo.get_by_id(question.paragraph_id)

    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {question.paragraph_id} not found"
        )

    chapter_repo = ChapterRepository(db)
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)

    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {paragraph.chapter_id} not found"
        )

    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {chapter.textbook_id} not found"
        )

    if textbook.school_id is not None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="This embedded question belongs to a non-global textbook. Use school admin endpoints."
        )

    return question, paragraph, chapter, textbook
