"""
Global Paragraph Outcomes (GOSO mapping) endpoints for SUPER_ADMIN.
Links global paragraphs to learning outcomes from GOSO.
"""

from typing import Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.textbook import Textbook
from app.models.chapter import Chapter
from app.models.paragraph import Paragraph
from app.models.goso import ParagraphOutcome
from app.repositories.paragraph_repo import ParagraphRepository
from app.repositories.goso_repo import GosoRepository, ParagraphOutcomeRepository
from app.schemas.goso import (
    ParagraphOutcomeCreate,
    ParagraphOutcomeUpdate,
    ParagraphOutcomeResponse,
    ParagraphOutcomeWithDetails,
)
from ._dependencies import require_global_paragraph


router = APIRouter()


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
    from app.repositories.chapter_repo import ChapterRepository
    from app.repositories.textbook_repo import TextbookRepository

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
    paragraph_data: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db)
):
    """
    Get all outcomes linked to a global paragraph (SUPER_ADMIN only).

    Returns all learning outcomes mapped to the specified paragraph.
    """
    paragraph, _, _ = paragraph_data
    po_repo = ParagraphOutcomeRepository(db)

    # Get links with outcome details
    links = await po_repo.get_by_paragraph(paragraph.id, load_outcome=True)

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
