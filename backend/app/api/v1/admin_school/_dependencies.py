"""
Reusable dependencies for School Admin API.

These dependencies encapsulate common access checks to eliminate code duplication
across admin_school endpoints. Each dependency handles:
1. Entity existence check (404 if not found)
2. School ownership verification (403 if wrong school)
3. Global vs school content distinction (403 for write ops on global)
"""

from typing import Tuple
from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.api.dependencies import get_current_user_school_id
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.school_class import SchoolClass
from app.models.user import User


# =============================================================================
# Content Access Dependencies (Textbook -> Chapter -> Paragraph hierarchy)
# =============================================================================

async def get_textbook_for_school_admin(
    textbook_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Textbook:
    """
    Get textbook with school access verification for ADMIN (read operations).

    Access rules:
    - Global textbooks (school_id = NULL) - allowed (read-only)
    - School textbooks (school_id = current) - allowed
    - Other school textbooks - 403
    """
    from app.repositories.textbook_repo import TextbookRepository
    repo = TextbookRepository(db)
    textbook = await repo.get_by_id(textbook_id)

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

    return textbook


async def require_school_textbook(
    textbook_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Textbook:
    """
    Require school-owned textbook for write operations.
    Raises 403 for global textbooks.
    """
    from app.repositories.textbook_repo import TextbookRepository
    repo = TextbookRepository(db)
    textbook = await repo.get_by_id(textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Textbook {textbook_id} not found"
        )

    if textbook.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify global textbooks. Contact SUPER_ADMIN."
        )

    if textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this textbook"
        )

    return textbook


async def get_chapter_for_school_admin(
    chapter_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Chapter:
    """
    Get chapter with school access verification (read operations).
    Eager loads parent textbook for access check.
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

    if textbook and textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    return chapter


async def require_school_chapter(
    chapter_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Tuple[Chapter, Textbook]:
    """
    Require chapter in school-owned textbook for write operations.
    Returns tuple (chapter, textbook) for convenience.
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
            detail="Parent textbook not found"
        )

    if textbook.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify chapters in global textbooks. Contact SUPER_ADMIN."
        )

    if textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this chapter"
        )

    return chapter, textbook


async def get_paragraph_for_school_admin(
    paragraph_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Paragraph:
    """
    Get paragraph with school access verification (read operations).
    Traverses chapter -> textbook for access check.
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
            detail="Parent chapter not found"
        )

    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)

    if textbook and textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    return paragraph


async def require_school_paragraph(
    paragraph_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Tuple[Paragraph, Chapter, Textbook]:
    """
    Require paragraph in school-owned textbook for write operations.
    Returns tuple (paragraph, chapter, textbook) for convenience.
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
            detail="Parent chapter not found"
        )

    textbook_repo = TextbookRepository(db)
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)

    if not textbook:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent textbook not found"
        )

    if textbook.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify paragraphs in global textbooks. Contact SUPER_ADMIN."
        )

    if textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this paragraph"
        )

    return paragraph, chapter, textbook


# =============================================================================
# Test Access Dependencies (Test -> Question -> Option hierarchy)
# =============================================================================

async def get_test_for_school_admin(
    test_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Test:
    """
    Get test with school access verification (read operations).
    """
    from app.repositories.test_repo import TestRepository
    repo = TestRepository(db)
    test = await repo.get_by_id(test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    return test


async def require_school_test(
    test_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Test:
    """
    Require school-owned test for write operations.
    """
    from app.repositories.test_repo import TestRepository
    repo = TestRepository(db)
    test = await repo.get_by_id(test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Test {test_id} not found"
        )

    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify global tests. Contact SUPER_ADMIN."
        )

    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this test"
        )

    return test


async def get_question_for_school_admin(
    question_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Question:
    """
    Get question with parent test access verification (read operations).
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

    if test and test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this question"
        )

    return question


async def require_school_question(
    question_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Tuple[Question, Test]:
    """
    Require question in school-owned test for write operations.
    Returns tuple (question, test) for convenience.
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
            detail="Parent test not found"
        )

    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify questions in global tests. Contact SUPER_ADMIN."
        )

    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this question"
        )

    return question, test


async def get_option_for_school_admin(
    option_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> QuestionOption:
    """
    Get question option with parent question/test access verification.
    """
    from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
    from app.repositories.test_repo import TestRepository

    option_repo = QuestionOptionRepository(db)
    option = await option_repo.get_by_id(option_id)

    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option {option_id} not found"
        )

    question_repo = QuestionRepository(db)
    question = await question_repo.get_by_id(option.question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent question not found"
        )

    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(question.test_id, load_questions=False)

    if test and test.school_id is not None and test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this option"
        )

    return option


async def require_school_option(
    option_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Tuple[QuestionOption, Question, Test]:
    """
    Require option in school-owned test for write operations.
    Returns tuple (option, question, test).
    """
    from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
    from app.repositories.test_repo import TestRepository

    option_repo = QuestionOptionRepository(db)
    option = await option_repo.get_by_id(option_id)

    if not option:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Option {option_id} not found"
        )

    question_repo = QuestionRepository(db)
    question = await question_repo.get_by_id(option.question_id)

    if not question:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent question not found"
        )

    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(question.test_id, load_questions=False)

    if not test:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Parent test not found"
        )

    if test.school_id is None:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot modify options in global tests. Contact SUPER_ADMIN."
        )

    if test.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this option"
        )

    return option, question, test


# =============================================================================
# User Management Dependencies
# =============================================================================

async def get_user_for_school_admin(
    user_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get user with school ownership verification.
    """
    from app.repositories.user_repo import UserRepository
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    if user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )

    return user


async def get_student_for_school_admin(
    student_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Student:
    """
    Get student with school ownership verification.
    Eager loads user and classes.
    """
    from app.repositories.student_repo import StudentRepository
    repo = StudentRepository(db)
    student = await repo.get_by_id(student_id, school_id, load_user=True, load_classes=True)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )

    return student


async def get_teacher_for_school_admin(
    teacher_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Teacher:
    """
    Get teacher with school ownership verification.
    Eager loads user and classes.
    """
    from app.repositories.teacher_repo import TeacherRepository
    repo = TeacherRepository(db)
    teacher = await repo.get_by_id(teacher_id, school_id, load_user=True, load_classes=True)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher {teacher_id} not found"
        )

    return teacher


async def get_parent_for_school_admin(
    parent_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> Parent:
    """
    Get parent with school ownership verification.
    Eager loads user and children.
    """
    from app.repositories.parent_repo import ParentRepository
    repo = ParentRepository(db)
    parent = await repo.get_by_id(parent_id, school_id, load_user=True, load_children=True)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent {parent_id} not found"
        )

    return parent


async def get_class_for_school_admin(
    class_id: int,
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
) -> SchoolClass:
    """
    Get school class with ownership verification.
    Eager loads students and teachers.
    """
    from app.repositories.school_class_repo import SchoolClassRepository
    repo = SchoolClassRepository(db)
    school_class = await repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)

    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    return school_class
