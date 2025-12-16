"""
GOSO (State Educational Standard) API endpoints.

Read-only endpoints for accessing GOSO data: subjects, frameworks, sections,
subsections, learning outcomes, and paragraph-outcome mappings.
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.repositories.goso_repo import GosoRepository, ParagraphOutcomeRepository
from app.schemas.goso import (
    SubjectResponse,
    SubjectListResponse,
    FrameworkResponse,
    FrameworkListResponse,
    FrameworkWithSections,
    GosoSectionListResponse,
    LearningOutcomeListResponse,
    LearningOutcomeWithContext,
    ParagraphOutcomeWithDetails,
)


router = APIRouter()


# ==================== Subjects ====================

@router.get("/subjects", response_model=List[SubjectListResponse])
async def list_subjects(
    is_active: bool = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of all subjects.

    Returns list of subjects (предметы) available in the system.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    subjects = await repo.get_all_subjects(is_active=is_active)
    return subjects


@router.get("/subjects/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get subject by ID.

    Returns detailed information about a specific subject.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    subject = await repo.get_subject_by_id(subject_id)

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Subject with id {subject_id} not found"
        )

    return subject


# ==================== Frameworks ====================

@router.get("/frameworks", response_model=List[FrameworkListResponse])
async def list_frameworks(
    subject_id: Optional[int] = Query(None, description="Filter by subject ID"),
    is_active: bool = Query(True, description="Filter by active status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of GOSO frameworks (versions).

    Returns list of educational standard versions (versions of ГОСО).
    Can be filtered by subject.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    frameworks = await repo.get_all_frameworks(
        subject_id=subject_id,
        is_active=is_active
    )
    return frameworks


@router.get("/frameworks/{framework_id}", response_model=FrameworkResponse)
async def get_framework(
    framework_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get framework by ID.

    Returns detailed information about a specific GOSO framework.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    framework = await repo.get_framework_by_id(framework_id)

    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework with id {framework_id} not found"
        )

    return framework


@router.get("/frameworks/{framework_id}/structure", response_model=FrameworkWithSections)
async def get_framework_structure(
    framework_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get framework with full structure (sections and subsections).

    Returns the framework with nested sections and subsections.
    Useful for displaying the full GOSO structure in UI.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    framework = await repo.get_framework_by_id(framework_id, load_structure=True)

    if not framework:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Framework with id {framework_id} not found"
        )

    # Build nested response
    sections_list = []
    for section in framework.sections:
        section_data = GosoSectionListResponse.model_validate(section)
        sections_list.append(section_data)

    # Sort sections by display_order
    sections_list.sort(key=lambda x: x.display_order)

    # Build response with sections
    response_data = FrameworkResponse.model_validate(framework).model_dump()
    response_data["sections"] = [s.model_dump() for s in sections_list]

    return FrameworkWithSections(**response_data)


# ==================== Learning Outcomes ====================

@router.get("/outcomes", response_model=List[LearningOutcomeListResponse])
async def list_outcomes(
    framework_id: Optional[int] = Query(None, description="Filter by framework ID"),
    grade: Optional[int] = Query(None, ge=1, le=11, description="Filter by grade (1-11)"),
    subsection_id: Optional[int] = Query(None, description="Filter by subsection ID"),
    section_id: Optional[int] = Query(None, description="Filter by section ID"),
    is_active: bool = Query(True, description="Filter by active status"),
    limit: int = Query(100, ge=1, le=1000, description="Limit results"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of learning outcomes.

    Returns list of learning outcomes (цели обучения) with optional filters.
    Can be filtered by framework, grade, section, or subsection.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    outcomes = await repo.get_outcomes(
        framework_id=framework_id,
        grade=grade,
        subsection_id=subsection_id,
        section_id=section_id,
        is_active=is_active,
        limit=limit,
        offset=offset
    )
    return outcomes


@router.get("/outcomes/{outcome_id}", response_model=LearningOutcomeWithContext)
async def get_outcome(
    outcome_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get learning outcome by ID with full context.

    Returns the learning outcome with section and subsection names.
    Useful for displaying the outcome with its full context.
    Requires authentication (any role).
    """
    repo = GosoRepository(db)
    context = await repo.get_outcome_with_context(outcome_id)

    if not context:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Learning outcome with id {outcome_id} not found"
        )

    outcome = context["outcome"]

    # Build response with context
    response_data = {
        "id": outcome.id,
        "framework_id": outcome.framework_id,
        "subsection_id": outcome.subsection_id,
        "grade": outcome.grade,
        "code": outcome.code,
        "title_ru": outcome.title_ru,
        "title_kz": outcome.title_kz,
        "description_ru": outcome.description_ru,
        "description_kz": outcome.description_kz,
        "cognitive_level": outcome.cognitive_level,
        "display_order": outcome.display_order,
        "is_active": outcome.is_active,
        "created_at": outcome.created_at,
        "updated_at": outcome.updated_at,
        "deleted_at": outcome.deleted_at,
        "is_deleted": outcome.is_deleted,
        "section_code": context["section_code"],
        "section_name_ru": context["section_name_ru"],
        "subsection_code": context["subsection_code"],
        "subsection_name_ru": context["subsection_name_ru"],
    }

    return LearningOutcomeWithContext(**response_data)


# ==================== Paragraph Outcomes ====================

@router.get("/paragraphs/{paragraph_id}/outcomes", response_model=List[ParagraphOutcomeWithDetails])
async def get_paragraph_outcomes(
    paragraph_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all learning outcomes linked to a paragraph.

    Returns list of paragraph-outcome links with outcome details.
    Shows which learning outcomes are covered by the paragraph.
    Requires authentication (any role).
    """
    repo = ParagraphOutcomeRepository(db)
    links = await repo.get_by_paragraph(paragraph_id, load_outcome=True)

    # Build response with outcome details
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
