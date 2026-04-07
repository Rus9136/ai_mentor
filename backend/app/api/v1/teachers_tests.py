"""
Teacher Test Management API.

Teachers can view, create, edit and delete school tests
filtered by their subject (teacher.subject_id -> textbook.subject_id).
"""

from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import (
    require_teacher,
    get_teacher_from_user,
    get_current_user_school_id,
    get_pagination_params,
)
from app.models.user import User
from app.models.teacher import Teacher
from app.models.test import Test, Question, QuestionOption, QuestionType
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.test_repo import TestRepository
from app.repositories.question_repo import QuestionRepository, QuestionOptionRepository
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
    QuestionOptionCreate,
    QuestionOptionUpdate,
    QuestionOptionResponse,
)
from app.schemas.pagination import PaginatedResponse, PaginationParams


router = APIRouter(prefix="/teachers/tests", tags=["Teachers - Tests"])


# =============================================================================
# Helper dependencies
# =============================================================================


async def _get_test_for_teacher(
    test_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
) -> Test:
    """
    Get test by ID with read access check.
    Teacher can read global tests and school tests of their subject.
    """
    test_repo = TestRepository(db)
    test = await test_repo.get_by_id(test_id)
    if not test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Check school access
    if test.school_id is not None and test.school_id != school_id:
        raise HTTPException(status_code=403, detail="Access denied")

    # Check subject match via textbook (multi-subject)
    teacher_sids = teacher.subject_ids
    if test.textbook_id and teacher_sids:
        textbook_repo = TextbookRepository(db)
        textbook = await textbook_repo.get_by_id(test.textbook_id)
        if textbook and textbook.subject_id not in teacher_sids:
            raise HTTPException(status_code=403, detail="Test does not belong to your subjects")

    return test


async def _require_school_test_for_teacher(
    test_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
) -> Test:
    """
    Get test by ID with write access check.
    Teacher can only modify school tests (not global) of their subject.
    """
    test = await _get_test_for_teacher(test_id, teacher, school_id, db)

    if test.school_id is None:
        raise HTTPException(status_code=403, detail="Cannot modify global tests")

    return test


# =============================================================================
# IMPORTANT: Static-prefix routes (/questions/*, /options/*) MUST be declared
# BEFORE /{test_id} to avoid FastAPI matching "questions" as test_id.
# =============================================================================


# =============================================================================
# Question CRUD (static prefix — must come before /{test_id})
# =============================================================================


@router.put("/questions/{question_id}")
async def update_teacher_question(
    question_id: int,
    data: QuestionUpdate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a question in a school test."""
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    test = await _require_school_test_for_teacher(question.test_id, teacher, school_id, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(question, field, value)

    updated_question = await question_repo.update(question)
    options = await option_repo.get_by_question(updated_question.id)

    return {
        "id": updated_question.id,
        "test_id": updated_question.test_id,
        "sort_order": updated_question.sort_order,
        "question_type": updated_question.question_type.value
        if hasattr(updated_question.question_type, "value")
        else updated_question.question_type,
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
        ],
    }


@router.delete("/questions/{question_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher_question(
    question_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a question in a school test."""
    question_repo = QuestionRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await _require_school_test_for_teacher(question.test_id, teacher, school_id, db)
    await question_repo.soft_delete(question)


@router.post("/questions/{question_id}/options", response_model=QuestionOptionResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher_option(
    question_id: int,
    data: QuestionOptionCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Create a new option for a question in a school test."""
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    question = await question_repo.get_by_id(question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await _require_school_test_for_teacher(question.test_id, teacher, school_id, db)

    option = QuestionOption(question_id=question_id, **data.model_dump())
    return await option_repo.create(option)


# =============================================================================
# Option CRUD (static prefix — must come before /{test_id})
# =============================================================================


@router.put("/options/{option_id}")
async def update_teacher_option(
    option_id: int,
    data: QuestionOptionUpdate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a question option in a school test."""
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    option = await option_repo.get_by_id(option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    question = await question_repo.get_by_id(option.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await _require_school_test_for_teacher(question.test_id, teacher, school_id, db)

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(option, field, value)

    updated_option = await option_repo.update(option)

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
async def delete_teacher_option(
    option_id: int,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a question option in a school test."""
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    option = await option_repo.get_by_id(option_id)
    if not option:
        raise HTTPException(status_code=404, detail="Option not found")

    question = await question_repo.get_by_id(option.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    await _require_school_test_for_teacher(question.test_id, teacher, school_id, db)
    await option_repo.soft_delete(option)


# =============================================================================
# Test CRUD (/{test_id} routes — AFTER static-prefix routes)
# =============================================================================


@router.get("", response_model=PaginatedResponse[TestListResponse])
async def list_teacher_tests(
    include_global: bool = Query(True, description="Include global tests"),
    chapter_id: Optional[int] = Query(None, description="Filter by chapter ID"),
    grade_level: Optional[int] = Query(None, ge=1, le=11, description="Filter by grade level (1-11)"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=500, description="Items per page (max 500 for tree view)"),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    List tests filtered by teacher's subjects.
    Returns global + school tests for textbooks matching teacher's subject(s).
    """
    test_repo = TestRepository(db)

    teacher_sids = teacher.subject_ids or None
    tests, total = await test_repo.get_by_school_paginated(
        school_id=school_id,
        page=page,
        page_size=page_size,
        include_global=include_global,
        chapter_id=chapter_id,
        subject_ids=teacher_sids,
        grade_level=grade_level,
    )

    items = [TestListResponse.from_test(t) for t in tests]
    return PaginatedResponse.create(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


@router.post("", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def create_teacher_test(
    data: TestCreate,
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Create a new school test. Validates textbook belongs to teacher's subject.
    """
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)
    paragraph_repo = ParagraphRepository(db)
    test_repo = TestRepository(db)

    # Validate textbook exists and belongs to school or is global
    textbook = await textbook_repo.get_by_id(data.textbook_id)
    if not textbook:
        raise HTTPException(status_code=404, detail=f"Textbook {data.textbook_id} not found")
    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(status_code=403, detail="Cannot create test for textbook from another school")

    # Validate textbook subject matches teacher's subjects
    teacher_sids = teacher.subject_ids
    if teacher_sids and textbook.subject_id not in teacher_sids:
        raise HTTPException(status_code=403, detail="Textbook does not belong to your subjects")

    # Validate chapter hierarchy
    if data.chapter_id:
        chapter = await chapter_repo.get_by_id(data.chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail=f"Chapter {data.chapter_id} not found")
        if chapter.textbook_id != data.textbook_id:
            raise HTTPException(
                status_code=400,
                detail=f"Chapter {data.chapter_id} does not belong to textbook {data.textbook_id}",
            )

    # Validate paragraph hierarchy
    if data.paragraph_id:
        if not data.chapter_id:
            raise HTTPException(status_code=400, detail="paragraph_id requires chapter_id to be set")
        paragraph = await paragraph_repo.get_by_id(data.paragraph_id)
        if not paragraph:
            raise HTTPException(status_code=404, detail=f"Paragraph {data.paragraph_id} not found")
        if paragraph.chapter_id != data.chapter_id:
            raise HTTPException(
                status_code=400,
                detail=f"Paragraph {data.paragraph_id} does not belong to chapter {data.chapter_id}",
            )

    test = Test(
        school_id=school_id,
        textbook_id=data.textbook_id,
        title=data.title,
        description=data.description,
        chapter_id=data.chapter_id,
        paragraph_id=data.paragraph_id,
        test_purpose=data.test_purpose,
        difficulty=data.difficulty,
        time_limit=data.time_limit,
        passing_score=data.passing_score,
        is_active=data.is_active,
    )

    return await test_repo.create(test)


@router.post("/{test_id}/clone", response_model=TestResponse, status_code=status.HTTP_201_CREATED)
async def clone_test_for_teacher(
    test_id: int,
    test: Test = Depends(_get_test_for_teacher),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """
    Clone a test (global or school) into a new school-specific copy.
    Copies all questions and options. Teacher can then edit the copy.
    """
    test_repo = TestRepository(db)
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    # Load full test with questions and options
    full_test = await test_repo.get_by_id(test_id, load_questions=True)
    if not full_test:
        raise HTTPException(status_code=404, detail="Test not found")

    # Create cloned test
    cloned_test = Test(
        school_id=school_id,
        source_test_id=full_test.id,
        textbook_id=full_test.textbook_id,
        chapter_id=full_test.chapter_id,
        paragraph_id=full_test.paragraph_id,
        title=f"{full_test.title} (адаптированный)",
        description=full_test.description,
        test_purpose=full_test.test_purpose,
        difficulty=full_test.difficulty,
        time_limit=full_test.time_limit,
        passing_score=full_test.passing_score,
        is_active=full_test.is_active,
    )
    cloned_test = await test_repo.create(cloned_test)

    # Clone questions and options
    for question in (full_test.questions or []):
        if question.is_deleted:
            continue
        new_question = Question(
            test_id=cloned_test.id,
            sort_order=question.sort_order,
            question_type=question.question_type,
            question_text=question.question_text,
            explanation=question.explanation,
            points=question.points,
        )
        new_question = await question_repo.create(new_question)

        for option in (question.options or []):
            if option.is_deleted:
                continue
            new_option = QuestionOption(
                question_id=new_question.id,
                sort_order=option.sort_order,
                option_text=option.option_text,
                is_correct=option.is_correct,
            )
            await option_repo.create(new_option)

    return cloned_test


@router.get("/{test_id}", response_model=TestResponse)
async def get_teacher_test(
    test: Test = Depends(_get_test_for_teacher),
):
    """Get a specific test by ID (read access: global + own school + own subject)."""
    return test


@router.put("/{test_id}", response_model=TestResponse)
async def update_teacher_test(
    data: TestUpdate,
    test: Test = Depends(_require_school_test_for_teacher),
    teacher: Teacher = Depends(get_teacher_from_user),
    school_id: int = Depends(get_current_user_school_id),
    db: AsyncSession = Depends(get_db),
):
    """Update a school test (only school tests of teacher's subject)."""
    test_repo = TestRepository(db)
    textbook_repo = TextbookRepository(db)
    chapter_repo = ChapterRepository(db)
    paragraph_repo = ParagraphRepository(db)

    update_data = data.model_dump(exclude_unset=True)

    new_textbook_id = update_data.get("textbook_id", test.textbook_id)
    new_chapter_id = update_data.get("chapter_id", test.chapter_id)
    new_paragraph_id = update_data.get("paragraph_id", test.paragraph_id)

    # Validate textbook if changed
    if "textbook_id" in update_data and update_data["textbook_id"] is not None:
        textbook = await textbook_repo.get_by_id(update_data["textbook_id"])
        if not textbook:
            raise HTTPException(status_code=404, detail=f"Textbook {update_data['textbook_id']} not found")
        if textbook.school_id is not None and textbook.school_id != school_id:
            raise HTTPException(status_code=403, detail="Cannot assign test to textbook from another school")
        teacher_sids = teacher.subject_ids
        if teacher_sids and textbook.subject_id not in teacher_sids:
            raise HTTPException(status_code=403, detail="Textbook does not belong to your subjects")

    # Validate chapter
    if new_chapter_id:
        chapter = await chapter_repo.get_by_id(new_chapter_id)
        if not chapter:
            raise HTTPException(status_code=404, detail=f"Chapter {new_chapter_id} not found")
        if new_textbook_id and chapter.textbook_id != new_textbook_id:
            raise HTTPException(
                status_code=400,
                detail=f"Chapter {new_chapter_id} does not belong to textbook {new_textbook_id}",
            )

    # Validate paragraph
    if new_paragraph_id:
        if not new_chapter_id:
            raise HTTPException(status_code=400, detail="paragraph_id requires chapter_id to be set")
        paragraph = await paragraph_repo.get_by_id(new_paragraph_id)
        if not paragraph:
            raise HTTPException(status_code=404, detail=f"Paragraph {new_paragraph_id} not found")
        if paragraph.chapter_id != new_chapter_id:
            raise HTTPException(
                status_code=400,
                detail=f"Paragraph {new_paragraph_id} does not belong to chapter {new_chapter_id}",
            )

    for field, value in update_data.items():
        setattr(test, field, value)

    return await test_repo.update(test)


@router.delete("/{test_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_teacher_test(
    test: Test = Depends(_require_school_test_for_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Soft delete a school test (only school tests of teacher's subject)."""
    test_repo = TestRepository(db)
    await test_repo.soft_delete(test)


# =============================================================================
# Test-scoped Question routes (/{test_id}/questions — safe, no conflict)
# =============================================================================


@router.post("/{test_id}/questions", status_code=status.HTTP_201_CREATED)
async def create_teacher_question(
    test_id: int,
    data: QuestionCreate,
    test: Test = Depends(_require_school_test_for_teacher),
    db: AsyncSession = Depends(get_db),
):
    """Create a new question in a school test (with nested options)."""
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    options_data = data.options
    question_data = data.model_dump(exclude={"options"})

    question = Question(test_id=test_id, **question_data)
    created_question = await question_repo.create(question)

    created_options = []
    if options_data:
        for option_create in options_data:
            option = QuestionOption(
                question_id=created_question.id,
                **option_create.model_dump(),
            )
            created_option = await option_repo.create(option)
            created_options.append(created_option)

    return {
        "id": created_question.id,
        "test_id": created_question.test_id,
        "sort_order": created_question.sort_order,
        "question_type": created_question.question_type.value
        if hasattr(created_question.question_type, "value")
        else created_question.question_type,
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
        ],
    }


@router.get("/{test_id}/questions", response_model=PaginatedResponse[QuestionResponse])
async def list_teacher_questions(
    test_id: int,
    test: Test = Depends(_get_test_for_teacher),
    pagination: PaginationParams = Depends(get_pagination_params),
    question_type: Optional[QuestionType] = Query(None),
    db: AsyncSession = Depends(get_db),
):
    """List questions for a test (read access)."""
    question_repo = QuestionRepository(db)
    option_repo = QuestionOptionRepository(db)

    questions, total = await question_repo.get_by_test_paginated(
        test_id=test_id,
        page=pagination.page,
        page_size=pagination.page_size,
        question_type=question_type,
    )

    result = []
    for question in questions:
        options = await option_repo.get_by_question(question.id)
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
            ],
        }
        result.append(QuestionResponse(**q_dict))

    return PaginatedResponse.create(result, total, pagination.page, pagination.page_size)
