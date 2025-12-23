"""
School content management API for ADMIN.
Manages school-specific textbooks, chapters, paragraphs, and customization (fork).
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User, UserRole
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.test import Test, Question, QuestionOption
from app.models.student import Student
from app.models.teacher import Teacher
from app.models.parent import Parent
from app.models.school_class import SchoolClass
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
from app.repositories.goso_repo import GosoRepository, ParagraphOutcomeRepository
from app.models.goso import ParagraphOutcome
from app.repositories.user_repo import UserRepository
from app.repositories.student_repo import StudentRepository
from app.repositories.teacher_repo import TeacherRepository
from app.repositories.parent_repo import ParentRepository
from app.repositories.school_class_repo import SchoolClassRepository
from app.core.security import get_password_hash
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
from app.schemas.user import (
    UserResponseSchema,
    UserUpdate,
)
from app.schemas.student import (
    StudentCreate,
    StudentUpdate,
    StudentResponse,
    StudentListResponse,
)
from app.schemas.teacher import (
    TeacherCreate,
    TeacherUpdate,
    TeacherResponse,
    TeacherListResponse,
)
from app.schemas.parent import (
    ParentCreate,
    ParentUpdate,
    ParentResponse,
    ParentListResponse,
    AddChildrenRequest,
    StudentBriefResponse,
)
from app.schemas.school_class import (
    SchoolClassCreate,
    SchoolClassUpdate,
    SchoolClassResponse,
    SchoolClassListResponse,
    AddStudentsRequest,
    AddTeachersRequest,
)
from app.schemas.school import (
    SchoolUpdate,
    SchoolResponse,
)
from app.schemas.goso import (
    ParagraphOutcomeCreate,
    ParagraphOutcomeUpdate,
    ParagraphOutcomeResponse,
    ParagraphOutcomeWithDetails,
)
from app.repositories.school_repo import SchoolRepository

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


@router.get("/chapters/{chapter_id}", response_model=ChapterResponse)
async def get_school_chapter(
    chapter_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single chapter from a school textbook (ADMIN only).
    Can access chapters from both global and school textbooks.
    """
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    chapter = await chapter_repo.get_by_id(chapter_id)
    if not chapter:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Chapter {chapter_id} not found"
        )

    # Verify access to parent textbook
    textbook = await textbook_repo.get_by_id(chapter.textbook_id)
    if textbook:
        # Allow access to global textbooks (school_id = null) and own school textbooks
        if textbook.school_id is not None and textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this chapter"
            )

    return chapter


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


@router.get("/paragraphs/{paragraph_id}", response_model=ParagraphResponse)
async def get_school_paragraph(
    paragraph_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a single paragraph from a school chapter (ADMIN only).
    Can access paragraphs from both global and school chapters.
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

    # Verify access to parent chapter and textbook
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook:
            # Allow access to global textbooks (school_id = null) and own school textbooks
            if textbook.school_id is not None and textbook.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this paragraph"
                )

    return paragraph


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
        school_id=school_id,  # School-specific test
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
    test = await test_repo.get_by_id(test_id, load_questions=False)

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
    Cannot update global tests. Validates hierarchical consistency.
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

@router.post("/tests/{test_id}/questions", status_code=status.HTTP_201_CREATED)
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
    Supports creating question with nested options in a single request.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

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
async def list_school_questions(
    test_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all questions for a test (ADMIN only).
    Can access questions from global and own school tests.

    Returns questions with options loaded manually in the same session
    to avoid RLS session variable issues with eager loading.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

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


@router.put("/questions/{question_id}")
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


@router.put("/options/{option_id}")
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


# ========== User Management Endpoints ==========

@router.get("/users", response_model=List[UserResponseSchema])
async def list_school_users(
    role: str = None,
    is_active: bool = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all users for the school (ADMIN only).
    Optional filters: role, is_active.
    """
    from app.repositories.user_repo import UserRepository
    from app.schemas.user import UserResponseSchema

    user_repo = UserRepository(db)
    return await user_repo.get_by_school(school_id, role=role, is_active=is_active)


@router.get("/users/{user_id}", response_model=UserResponseSchema)
async def get_school_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific user by ID (ADMIN only).
    """
    from app.repositories.user_repo import UserRepository
    from app.schemas.user import UserResponseSchema

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Verify belongs to school
    if user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )

    return user


@router.put("/users/{user_id}", response_model=UserResponseSchema)
async def update_school_user(
    user_id: int,
    data: UserUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user info (ADMIN only).
    Can update: first_name, last_name, middle_name, phone.
    Cannot update: email, password, role.
    """
    from app.repositories.user_repo import UserRepository
    from app.schemas.user import UserResponseSchema, UserUpdate

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Verify belongs to school
    if user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )

    # Update only allowed fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    return await user_repo.update(user)


@router.post("/users/{user_id}/deactivate", response_model=UserResponseSchema)
async def deactivate_school_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate a user (set is_active=False) (ADMIN only).
    """
    from app.repositories.user_repo import UserRepository
    from app.schemas.user import UserResponseSchema

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Verify belongs to school
    if user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )

    return await user_repo.deactivate(user)


@router.post("/users/{user_id}/activate", response_model=UserResponseSchema)
async def activate_school_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate a user (set is_active=True) (ADMIN only).
    """
    from app.repositories.user_repo import UserRepository
    from app.schemas.user import UserResponseSchema

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Verify belongs to school
    if user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )

    return await user_repo.activate(user)


@router.delete("/users/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_user(
    user_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a user (ADMIN only).
    """
    from app.repositories.user_repo import UserRepository

    user_repo = UserRepository(db)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User {user_id} not found"
        )

    # Verify belongs to school
    if user.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this user"
        )

    await user_repo.soft_delete(user)


# ========== Student Management Endpoints ==========

@router.get("/students", response_model=List[StudentListResponse])
async def list_school_students(
    grade_level: int = None,
    class_id: int = None,
    is_active: bool = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all students for the school (ADMIN only).
    Optional filters: grade_level, class_id, is_active.
    """
    from app.repositories.student_repo import StudentRepository
    from app.schemas.student import StudentListResponse

    student_repo = StudentRepository(db)

    if grade_level is not None or class_id is not None or is_active is not None:
        return await student_repo.get_by_filters(
            school_id,
            grade_level=grade_level,
            class_id=class_id,
            is_active=is_active,
            load_user=True
        )
    else:
        return await student_repo.get_all(school_id, load_user=True)


@router.post("/students", response_model=StudentResponse, status_code=status.HTTP_201_CREATED)
async def create_school_student(
    data: StudentCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new student (ADMIN only).
    Creates both User and Student in a transaction.
    """
    user_repo = UserRepository(db)
    student_repo = StudentRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {data.email} already exists"
        )

    # Check if student_code already exists (if provided)
    if data.student_code:
        existing_student = await student_repo.get_by_student_code(data.student_code, school_id)
        if existing_student:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Student with code {data.student_code} already exists"
            )

    # Create user first
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.STUDENT,
        school_id=school_id,
        is_active=True
    )
    user = await user_repo.create(user)

    # Generate student_code if not provided
    student_code = data.student_code
    if not student_code:
        # Auto-generate: STU{grade}{year}{sequence}
        from datetime import datetime
        year = datetime.now().year % 100  # Last 2 digits
        count = await student_repo.count_by_school(school_id)
        student_code = f"STU{data.grade_level}{year:02d}{count+1:04d}"

    # Create student
    student = Student(
        school_id=school_id,
        user_id=user.id,
        student_code=student_code,
        grade_level=data.grade_level,
        birth_date=data.birth_date
    )
    student = await student_repo.create(student)

    # Load user relationship and classes
    student = await student_repo.get_by_id(student.id, school_id, load_user=True, load_classes=True)
    return student


@router.get("/students/{student_id}", response_model=StudentResponse)
async def get_school_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific student by ID (ADMIN only).
    """
    from app.repositories.student_repo import StudentRepository
    from app.schemas.student import StudentResponse

    student_repo = StudentRepository(db)
    student = await student_repo.get_by_id(
        student_id,
        school_id,
        load_user=True,
        load_classes=True
    )

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )

    return student


@router.put("/students/{student_id}", response_model=StudentResponse)
async def update_school_student(
    student_id: int,
    data: StudentUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update student info (ADMIN only).
    Can update: student_code, grade_level, birth_date.
    """
    from app.repositories.student_repo import StudentRepository
    from app.schemas.student import StudentResponse, StudentUpdate

    student_repo = StudentRepository(db)
    student = await student_repo.get_by_id(student_id, school_id)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(student, field, value)

    student = await student_repo.update(student)

    # Reload with relationships
    student = await student_repo.get_by_id(student_id, school_id, load_user=True, load_classes=True)
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_student(
    student_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a student (ADMIN only).
    """
    from app.repositories.student_repo import StudentRepository

    student_repo = StudentRepository(db)
    student = await student_repo.get_by_id(student_id, school_id)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Student {student_id} not found"
        )

    await student_repo.soft_delete(student)


# ========== Teacher Management Endpoints ==========

@router.get("/teachers", response_model=List[TeacherListResponse])
async def list_school_teachers(
    subject: str = None,
    class_id: int = None,
    is_active: bool = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all teachers for the school (ADMIN only).
    Optional filters: subject, class_id, is_active.
    """
    from app.repositories.teacher_repo import TeacherRepository
    from app.schemas.teacher import TeacherListResponse

    teacher_repo = TeacherRepository(db)

    if subject is not None or class_id is not None or is_active is not None:
        return await teacher_repo.get_by_filters(
            school_id,
            subject=subject,
            class_id=class_id,
            is_active=is_active,
            load_user=True
        )
    else:
        return await teacher_repo.get_all(school_id, load_user=True)


@router.post("/teachers", response_model=TeacherResponse, status_code=status.HTTP_201_CREATED)
async def create_school_teacher(
    data: TeacherCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new teacher (ADMIN only).
    Creates both User and Teacher in a transaction.
    """
    user_repo = UserRepository(db)
    teacher_repo = TeacherRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {data.email} already exists"
        )

    # Check if teacher_code already exists (if provided)
    if data.teacher_code:
        existing_teacher = await teacher_repo.get_by_teacher_code(data.teacher_code, school_id)
        if existing_teacher:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Teacher with code {data.teacher_code} already exists"
            )

    # Create user first
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.TEACHER,
        school_id=school_id,
        is_active=True
    )
    user = await user_repo.create(user)

    # Generate teacher_code if not provided
    teacher_code = data.teacher_code
    if not teacher_code:
        # Auto-generate: TCHR{year}{sequence}
        from datetime import datetime
        year = datetime.now().year % 100  # Last 2 digits
        count = await teacher_repo.count_by_school(school_id)
        teacher_code = f"TCHR{year:02d}{count+1:04d}"

    # Create teacher
    teacher = Teacher(
        school_id=school_id,
        user_id=user.id,
        teacher_code=teacher_code,
        subject=data.subject,
        bio=data.bio
    )
    teacher = await teacher_repo.create(teacher)

    # Load user relationship and classes
    teacher = await teacher_repo.get_by_id(teacher.id, school_id, load_user=True, load_classes=True)
    return teacher


@router.get("/teachers/{teacher_id}", response_model=TeacherResponse)
async def get_school_teacher(
    teacher_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific teacher by ID (ADMIN only).
    """
    from app.repositories.teacher_repo import TeacherRepository
    from app.schemas.teacher import TeacherResponse

    teacher_repo = TeacherRepository(db)
    teacher = await teacher_repo.get_by_id(
        teacher_id,
        school_id,
        load_user=True,
        load_classes=True
    )

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher {teacher_id} not found"
        )

    return teacher


@router.put("/teachers/{teacher_id}", response_model=TeacherResponse)
async def update_school_teacher(
    teacher_id: int,
    data: TeacherUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update teacher info (ADMIN only).
    Can update: teacher_code, subject, bio.
    """
    from app.repositories.teacher_repo import TeacherRepository
    from app.schemas.teacher import TeacherResponse, TeacherUpdate

    teacher_repo = TeacherRepository(db)
    teacher = await teacher_repo.get_by_id(teacher_id, school_id)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher {teacher_id} not found"
        )

    # Update fields
    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(teacher, field, value)

    teacher = await teacher_repo.update(teacher)

    # Reload with relationships
    teacher = await teacher_repo.get_by_id(teacher_id, school_id, load_user=True, load_classes=True)
    return teacher


@router.delete("/teachers/{teacher_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_teacher(
    teacher_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a teacher (ADMIN only).
    """
    from app.repositories.teacher_repo import TeacherRepository

    teacher_repo = TeacherRepository(db)
    teacher = await teacher_repo.get_by_id(teacher_id, school_id)

    if not teacher:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Teacher {teacher_id} not found"
        )

    await teacher_repo.soft_delete(teacher)


# ========== Parent Management Endpoints ==========

@router.get("/parents", response_model=List[ParentListResponse])
async def list_school_parents(
    is_active: bool = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all parents for the school (ADMIN only).
    Optional filter: is_active.
    """
    from app.repositories.parent_repo import ParentRepository
    from app.schemas.parent import ParentListResponse

    parent_repo = ParentRepository(db)

    if is_active is not None:
        return await parent_repo.get_by_filters(school_id, is_active=is_active, load_user=True)
    else:
        return await parent_repo.get_all(school_id, load_user=True)


@router.post("/parents", response_model=ParentResponse, status_code=status.HTTP_201_CREATED)
async def create_school_parent(
    data: ParentCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new parent (ADMIN only).
    Creates both User and Parent in a transaction.
    Optionally links initial children (students).
    """
    user_repo = UserRepository(db)
    parent_repo = ParentRepository(db)

    # Check if email already exists
    existing_user = await user_repo.get_by_email(data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"User with email {data.email} already exists"
        )

    # Create user first
    user = User(
        email=data.email,
        password_hash=get_password_hash(data.password),
        first_name=data.first_name,
        last_name=data.last_name,
        middle_name=data.middle_name,
        phone=data.phone,
        role=UserRole.PARENT,
        school_id=school_id,
        is_active=True
    )
    user = await user_repo.create(user)

    # Create parent
    parent = Parent(
        school_id=school_id,
        user_id=user.id
    )
    parent = await parent_repo.create(parent)

    # Add initial children if provided
    if data.student_ids:
        try:
            parent = await parent_repo.add_children(parent.id, data.student_ids)
        except ValueError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )

    # Load user relationship
    parent = await parent_repo.get_by_id(parent.id, school_id, load_user=True, load_children=True)
    return parent


@router.get("/parents/{parent_id}", response_model=ParentResponse)
async def get_school_parent(
    parent_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific parent by ID (ADMIN only).
    """
    from app.repositories.parent_repo import ParentRepository
    from app.schemas.parent import ParentResponse

    parent_repo = ParentRepository(db)
    parent = await parent_repo.get_by_id(
        parent_id,
        school_id,
        load_user=True,
        load_children=True
    )

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent {parent_id} not found"
        )

    return parent


@router.delete("/parents/{parent_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_parent(
    parent_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a parent (ADMIN only).
    """
    from app.repositories.parent_repo import ParentRepository

    parent_repo = ParentRepository(db)
    parent = await parent_repo.get_by_id(parent_id, school_id)

    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent {parent_id} not found"
        )

    await parent_repo.soft_delete(parent)


# Parent-Children Management

@router.get("/parents/{parent_id}/children", response_model=List[StudentBriefResponse])
async def get_parent_children(
    parent_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all children (students) for a parent (ADMIN only).
    """
    from app.repositories.parent_repo import ParentRepository
    from app.schemas.parent import StudentBriefResponse

    parent_repo = ParentRepository(db)
    return await parent_repo.get_children(parent_id, school_id)


@router.post("/parents/{parent_id}/children", response_model=ParentResponse)
async def add_parent_children(
    parent_id: int,
    data: AddChildrenRequest,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add children (students) to a parent (ADMIN only).
    """
    from app.repositories.parent_repo import ParentRepository
    from app.schemas.parent import ParentResponse, AddChildrenRequest

    parent_repo = ParentRepository(db)

    # Verify parent exists and belongs to school
    parent = await parent_repo.get_by_id(parent_id, school_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent {parent_id} not found"
        )

    try:
        parent = await parent_repo.add_children(parent_id, data.student_ids)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    parent = await parent_repo.get_by_id(parent_id, school_id, load_user=True, load_children=True)
    return parent


@router.delete("/parents/{parent_id}/children/{student_id}", response_model=ParentResponse)
async def remove_parent_child(
    parent_id: int,
    student_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a child (student) from a parent (ADMIN only).
    """
    from app.repositories.parent_repo import ParentRepository
    from app.schemas.parent import ParentResponse

    parent_repo = ParentRepository(db)

    # Verify parent exists and belongs to school
    parent = await parent_repo.get_by_id(parent_id, school_id)
    if not parent:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent {parent_id} not found"
        )

    parent = await parent_repo.remove_children(parent_id, [student_id])

    # Reload with relationships
    parent = await parent_repo.get_by_id(parent_id, school_id, load_user=True, load_children=True)
    return parent


# ========== School Class Management Endpoints ==========

@router.get("/classes", response_model=List[SchoolClassListResponse])
async def list_school_classes(
    grade_level: int = None,
    academic_year: str = None,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all classes for the school (ADMIN only).
    Optional filters: grade_level, academic_year.
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)

    if grade_level is not None or academic_year is not None:
        classes = await class_repo.get_by_filters(
            school_id,
            grade_level=grade_level,
            academic_year=academic_year,
            load_students=True,
            load_teachers=True
        )
    else:
        classes = await class_repo.get_all(school_id, load_students=True, load_teachers=True)

    # Add counts for response
    result = []
    for school_class in classes:
        class_dict = {
            "id": school_class.id,
            "name": school_class.name,
            "code": school_class.code,
            "grade_level": school_class.grade_level,
            "academic_year": school_class.academic_year,
            "students_count": len(school_class.students) if school_class.students else 0,
            "teachers_count": len(school_class.teachers) if school_class.teachers else 0,
            "created_at": school_class.created_at,
        }
        result.append(class_dict)

    return result


@router.post("/classes", response_model=SchoolClassResponse, status_code=status.HTTP_201_CREATED)
async def create_school_class(
    data: SchoolClassCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a new school class (ADMIN only).
    """
    from app.repositories.school_class_repo import SchoolClassRepository
    from app.models.school_class import SchoolClass

    class_repo = SchoolClassRepository(db)

    # Check if code already exists in this school
    existing_class = await class_repo.get_by_code(data.code, school_id)
    if existing_class:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Class with code {data.code} already exists in this school"
        )

    # Create class
    school_class = SchoolClass(
        school_id=school_id,
        name=data.name,
        code=data.code,
        grade_level=data.grade_level,
        academic_year=data.academic_year
    )
    school_class = await class_repo.create(school_class)

    # Return with counts
    return {
        "id": school_class.id,
        "school_id": school_class.school_id,
        "name": school_class.name,
        "code": school_class.code,
        "grade_level": school_class.grade_level,
        "academic_year": school_class.academic_year,
        "created_at": school_class.created_at,
        "updated_at": school_class.updated_at,
        "students_count": 0,
        "teachers_count": 0,
    }


@router.get("/classes/{class_id}", response_model=SchoolClassResponse)
async def get_school_class(
    class_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get a specific class by ID (ADMIN only).
    Includes students and teachers lists.
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)
    school_class = await class_repo.get_by_id(
        class_id,
        school_id,
        load_students=True,
        load_teachers=True
    )

    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    # Return SQLAlchemy model directly - FastAPI will serialize it via Pydantic
    return school_class


@router.put("/classes/{class_id}", response_model=SchoolClassResponse)
async def update_school_class(
    class_id: int,
    data: SchoolClassUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update class info (ADMIN only).
    Can update: name, grade_level, academic_year.
    Note: code is NOT updatable.
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)
    school_class = await class_repo.get_by_id(class_id, school_id)

    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    # Update fields
    if data.name is not None:
        school_class.name = data.name
    if data.grade_level is not None:
        school_class.grade_level = data.grade_level
    if data.academic_year is not None:
        school_class.academic_year = data.academic_year

    await class_repo.update(school_class)

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)

    # Return SQLAlchemy model directly - FastAPI will serialize it via Pydantic
    return school_class


@router.delete("/classes/{class_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_school_class(
    class_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Soft delete a class (ADMIN only).
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)
    school_class = await class_repo.get_by_id(class_id, school_id)

    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    await class_repo.soft_delete(school_class)


# ========== School Class Students Management ==========

@router.post("/classes/{class_id}/students", response_model=SchoolClassResponse)
async def add_students_to_class(
    class_id: int,
    data: AddStudentsRequest,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add students to a class (bulk operation, ADMIN only).
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)

    # Verify class exists
    school_class = await class_repo.get_by_id(class_id, school_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    # Add students
    try:
        await class_repo.add_students(class_id, data.student_ids, school_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)

    # Return SQLAlchemy model directly - FastAPI will serialize it via Pydantic
    return school_class


@router.delete("/classes/{class_id}/students/{student_id}", response_model=SchoolClassResponse)
async def remove_student_from_class(
    class_id: int,
    student_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a student from a class (ADMIN only).
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)

    # Verify class exists
    school_class = await class_repo.get_by_id(class_id, school_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    # Remove student
    await class_repo.remove_students(class_id, [student_id], school_id)

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)

    # Return SQLAlchemy model directly - FastAPI will serialize it via Pydantic
    return school_class


# ========== School Class Teachers Management ==========

@router.post("/classes/{class_id}/teachers", response_model=SchoolClassResponse)
async def add_teachers_to_class(
    class_id: int,
    data: AddTeachersRequest,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Add teachers to a class (bulk operation, ADMIN only).
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)

    # Verify class exists
    school_class = await class_repo.get_by_id(class_id, school_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    # Add teachers
    try:
        await class_repo.add_teachers(class_id, data.teacher_ids, school_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)

    # Return SQLAlchemy model directly - FastAPI will serialize it via Pydantic
    return school_class


@router.delete("/classes/{class_id}/teachers/{teacher_id}", response_model=SchoolClassResponse)
async def remove_teacher_from_class(
    class_id: int,
    teacher_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Remove a teacher from a class (ADMIN only).
    """
    from app.repositories.school_class_repo import SchoolClassRepository

    class_repo = SchoolClassRepository(db)

    # Verify class exists
    school_class = await class_repo.get_by_id(class_id, school_id)
    if not school_class:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Class {class_id} not found"
        )

    # Remove teacher
    await class_repo.remove_teachers(class_id, [teacher_id], school_id)

    # Reload with relationships
    school_class = await class_repo.get_by_id(class_id, school_id, load_students=True, load_teachers=True)

    # Return SQLAlchemy model directly - FastAPI will serialize it via Pydantic
    return school_class


# ========== School Settings Endpoints ==========


@router.get("/settings", response_model=SchoolResponse)
async def get_school_settings(
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get settings for the current school (ADMIN only).

    Returns the school information including contact details.
    School ADMIN can only view their own school's settings.
    """
    school_repo = SchoolRepository(db)

    school = await school_repo.get_by_id(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found"
        )

    return school


@router.put("/settings", response_model=SchoolResponse)
async def update_school_settings(
    data: SchoolUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update settings for the current school (ADMIN only).

    School ADMIN can update:
    - description
    - email
    - phone
    - address

    School ADMIN CANNOT update:
    - name (only SUPER_ADMIN)
    - code (only SUPER_ADMIN)
    - is_active (only SUPER_ADMIN)
    """
    school_repo = SchoolRepository(db)

    # Verify school exists
    school = await school_repo.get_by_id(school_id)
    if not school:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"School {school_id} not found"
        )

    # School ADMIN can only update certain fields
    # Don't allow updating name, code, is_active
    update_data = data.model_dump(exclude_unset=True)

    # Remove restricted fields if present
    restricted_fields = {"name", "code", "is_active"}
    for field in restricted_fields:
        update_data.pop(field, None)

    # Apply updates to school object
    for key, value in update_data.items():
        setattr(school, key, value)

    # Update school
    updated_school = await school_repo.update(school)

    return updated_school


# ========== Paragraph Outcomes Endpoints (GOSO mapping) ==========

@router.post("/paragraph-outcomes", response_model=ParagraphOutcomeResponse, status_code=status.HTTP_201_CREATED)
async def create_school_paragraph_outcome(
    data: ParagraphOutcomeCreate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Create a paragraph-outcome link for a school or global paragraph (ADMIN only).

    School ADMIN can create mappings for:
    - Their own school's paragraphs (school_id matches)
    - Global paragraphs (school_id = NULL) - adds their own interpretation

    This mapping indicates which learning objectives are covered by the paragraph.
    """
    paragraph_repo = ParagraphRepository(db)
    goso_repo = GosoRepository(db)
    po_repo = ParagraphOutcomeRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    # 1. Check paragraph exists
    paragraph = await paragraph_repo.get_by_id(data.paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {data.paragraph_id} not found"
        )

    # 2. Verify access to paragraph
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

    # School ADMIN can create mappings for:
    # - Their own school's paragraphs
    # - Global paragraphs (adding their interpretation)
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create mapping for another school's paragraph"
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
async def get_school_paragraph_outcomes(
    paragraph_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all outcomes linked to a paragraph (ADMIN only).

    Returns all learning outcomes mapped to the specified paragraph.
    Accessible for school's own paragraphs and global paragraphs.
    """
    paragraph_repo = ParagraphRepository(db)
    po_repo = ParagraphOutcomeRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    # Check paragraph exists
    paragraph = await paragraph_repo.get_by_id(paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {paragraph_id} not found"
        )

    # Verify access to paragraph
    chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
    if chapter:
        textbook = await textbook_repo.get_by_id(chapter.textbook_id)
        if textbook and textbook.school_id is not None and textbook.school_id != school_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Cannot access another school's paragraph outcomes"
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
async def update_school_paragraph_outcome(
    outcome_link_id: int,
    data: ParagraphOutcomeUpdate,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Update a paragraph-outcome link (ADMIN only).

    Updates the confidence, anchor, or notes of an existing mapping.
    Can only update mappings created by users of the same school.
    """
    po_repo = ParagraphOutcomeRepository(db)
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    # Get existing link
    link = await po_repo.get_by_id(outcome_link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph-outcome link {outcome_link_id} not found"
        )

    # Verify access via paragraph's textbook
    paragraph = await paragraph_repo.get_by_id(link.paragraph_id)
    if paragraph:
        chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
        if chapter:
            textbook = await textbook_repo.get_by_id(chapter.textbook_id)
            # For school paragraphs, verify school ownership
            if textbook and textbook.school_id is not None and textbook.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot update mapping for another school's paragraph"
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
async def delete_school_paragraph_outcome(
    outcome_link_id: int,
    current_user: User = Depends(require_admin),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete a paragraph-outcome link (ADMIN only).

    Permanently removes the mapping between a paragraph and learning outcome.
    Can only delete mappings for own school's paragraphs.
    """
    po_repo = ParagraphOutcomeRepository(db)
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    # Get existing link
    link = await po_repo.get_by_id(outcome_link_id)
    if not link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph-outcome link {outcome_link_id} not found"
        )

    # Verify access via paragraph's textbook
    paragraph = await paragraph_repo.get_by_id(link.paragraph_id)
    if paragraph:
        chapter = await chapter_repo.get_by_id(paragraph.chapter_id)
        if chapter:
            textbook = await textbook_repo.get_by_id(chapter.textbook_id)
            # For school paragraphs, verify school ownership
            if textbook and textbook.school_id is not None and textbook.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete mapping for another school's paragraph"
                )

    await po_repo.delete(link)
