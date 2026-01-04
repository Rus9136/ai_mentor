"""
School Paragraph Outcomes (GOSO mapping) API for ADMIN.
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_admin, get_current_user_school_id
from app.models.user import User
from app.models.goso import ParagraphOutcome
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.chapter_repo import ChapterRepository
from app.repositories.textbook_repo import TextbookRepository
from app.repositories.goso_repo import GosoRepository, ParagraphOutcomeRepository
from app.schemas.goso import (
    ParagraphOutcomeCreate,
    ParagraphOutcomeUpdate,
    ParagraphOutcomeResponse,
    ParagraphOutcomeWithDetails,
)
from ._dependencies import get_paragraph_for_school_admin


router = APIRouter(tags=["School Paragraph Outcomes"])


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
    """
    paragraph_repo = ParagraphRepository(db)
    goso_repo = GosoRepository(db)
    po_repo = ParagraphOutcomeRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

    # Check paragraph exists
    paragraph = await paragraph_repo.get_by_id(data.paragraph_id)
    if not paragraph:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Paragraph {data.paragraph_id} not found"
        )

    # Verify access to paragraph
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

    if textbook.school_id is not None and textbook.school_id != school_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot create mapping for another school's paragraph"
        )

    # Check outcome exists and is active
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

    # Check for duplicate
    existing = await po_repo.get_by_paragraph_and_outcome(
        data.paragraph_id, data.outcome_id
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Mapping already exists between paragraph {data.paragraph_id} and outcome {data.outcome_id}"
        )

    # Create the link
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


@router.get("/paragraphs/{paragraph_id}/outcomes", response_model=List[ParagraphOutcomeWithDetails])
async def get_school_paragraph_outcomes(
    paragraph_id: int,
    paragraph=Depends(get_paragraph_for_school_admin),
    current_user: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all outcomes linked to a paragraph (ADMIN only).
    """
    po_repo = ParagraphOutcomeRepository(db)

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
    """
    po_repo = ParagraphOutcomeRepository(db)
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

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
    """
    po_repo = ParagraphOutcomeRepository(db)
    paragraph_repo = ParagraphRepository(db)
    chapter_repo = ChapterRepository(db)
    textbook_repo = TextbookRepository(db)

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
            if textbook and textbook.school_id is not None and textbook.school_id != school_id:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Cannot delete mapping for another school's paragraph"
                )

    await po_repo.delete(link)
