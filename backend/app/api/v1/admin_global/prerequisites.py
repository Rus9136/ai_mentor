"""
Global Prerequisite CRUD endpoints for SUPER_ADMIN.
Manages prerequisite links between paragraphs in global textbooks.
"""

from typing import List, Tuple
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.textbook import Textbook
from app.models.paragraph import Paragraph
from app.models.chapter import Chapter
from app.schemas.prerequisite import (
    PrerequisiteCreate,
    PrerequisiteResponse,
    TextbookGraphResponse,
)
from app.services.prerequisite_service import PrerequisiteService
from ._dependencies import require_global_paragraph, require_global_textbook

router = APIRouter()


@router.get(
    "/paragraphs/{paragraph_id}/prerequisites",
    response_model=List[PrerequisiteResponse],
)
async def list_prerequisites(
    paragraph_data: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all prerequisites for a global paragraph."""
    paragraph, chapter, textbook = paragraph_data

    service = PrerequisiteService(db)
    prereqs = await service.prereq_repo.get_prerequisites(paragraph.id)

    return [
        PrerequisiteResponse(
            id=p.id,
            paragraph_id=p.paragraph_id,
            prerequisite_paragraph_id=p.prerequisite_paragraph_id,
            strength=p.strength,
            created_at=p.created_at,
            prerequisite_title=p.prerequisite.title if p.prerequisite else None,
            prerequisite_number=p.prerequisite.number if p.prerequisite else None,
            prerequisite_chapter_title=(
                p.prerequisite.chapter.title
                if p.prerequisite and p.prerequisite.chapter else None
            ),
        )
        for p in prereqs
    ]


@router.post(
    "/paragraphs/{paragraph_id}/prerequisites",
    response_model=PrerequisiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_prerequisite(
    data: PrerequisiteCreate,
    paragraph_data: Tuple[Paragraph, Chapter, Textbook] = Depends(require_global_paragraph),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """
    Add a prerequisite to a global paragraph.
    Validates: same textbook, no circular dependency, no duplicate.
    """
    paragraph, chapter, textbook = paragraph_data

    service = PrerequisiteService(db)
    prereq = await service.add_prerequisite(
        paragraph_id=paragraph.id,
        prerequisite_paragraph_id=data.prerequisite_paragraph_id,
        strength=data.strength,
    )

    # Reload with relationships for response
    prereqs = await service.prereq_repo.get_prerequisites(paragraph.id)
    created = next((p for p in prereqs if p.id == prereq.id), prereq)

    return PrerequisiteResponse(
        id=created.id,
        paragraph_id=created.paragraph_id,
        prerequisite_paragraph_id=created.prerequisite_paragraph_id,
        strength=created.strength,
        created_at=created.created_at,
        prerequisite_title=created.prerequisite.title if created.prerequisite else None,
        prerequisite_number=created.prerequisite.number if created.prerequisite else None,
        prerequisite_chapter_title=(
            created.prerequisite.chapter.title
            if created.prerequisite and created.prerequisite.chapter else None
        ),
    )


@router.delete(
    "/prerequisites/{prereq_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def remove_prerequisite(
    prereq_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Remove a prerequisite link."""
    service = PrerequisiteService(db)
    await service.remove_prerequisite(prereq_id)


@router.get(
    "/textbooks/{textbook_id}/prerequisite-graph",
    response_model=TextbookGraphResponse,
)
async def get_textbook_prerequisite_graph(
    textbook: Textbook = Depends(require_global_textbook),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get full prerequisite graph for a textbook (for visualization)."""
    service = PrerequisiteService(db)
    return await service.get_textbook_graph(textbook.id)
