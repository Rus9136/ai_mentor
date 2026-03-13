"""
Daily Quest management endpoints for SUPER_ADMIN.
"""
import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.gamification import DailyQuest, QuestType
from app.models.textbook import Textbook
from app.models.paragraph import Paragraph
from app.repositories.gamification_repo import GamificationRepository
from app.schemas.gamification import (
    DailyQuestCreate,
    DailyQuestUpdate,
    DailyQuestAdminResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/daily-quests", tags=["Daily Quests (Global)"])


def _to_admin_response(quest: DailyQuest) -> DailyQuestAdminResponse:
    """Convert DailyQuest model to admin response with denormalized names."""
    return DailyQuestAdminResponse(
        id=quest.id,
        code=quest.code,
        name_kk=quest.name_kk,
        name_ru=quest.name_ru,
        description_kk=quest.description_kk,
        description_ru=quest.description_ru,
        quest_type=quest.quest_type.value if hasattr(quest.quest_type, 'value') else quest.quest_type,
        target_value=quest.target_value,
        xp_reward=quest.xp_reward,
        is_active=quest.is_active,
        school_id=quest.school_id,
        subject_id=quest.subject_id,
        textbook_id=quest.textbook_id,
        paragraph_id=quest.paragraph_id,
        subject_name=quest.subject.name_ru if quest.subject else None,
        textbook_title=quest.textbook.title if quest.textbook else None,
        paragraph_title=quest.paragraph.title if quest.paragraph else None,
        created_at=quest.created_at,
        updated_at=quest.updated_at,
    )


@router.get("", response_model=List[DailyQuestAdminResponse])
async def list_global_daily_quests(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all global daily quests."""
    repo = GamificationRepository(db)
    quests = await repo.list_daily_quests(school_id=None)
    return [_to_admin_response(q) for q in quests]


@router.post("", response_model=DailyQuestAdminResponse)
async def create_global_daily_quest(
    data: DailyQuestCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a global daily quest (school_id=NULL)."""
    # Validate quest_type
    try:
        qt = QuestType(data.quest_type)
    except ValueError:
        raise HTTPException(400, f"Invalid quest_type: {data.quest_type}. Valid: {[e.value for e in QuestType]}")

    # Validate FK references
    if data.subject_id:
        from app.models.subject import Subject
        result = await db.execute(select(Subject).where(Subject.id == data.subject_id))
        if not result.scalar_one_or_none():
            raise HTTPException(400, f"Subject {data.subject_id} not found")

    if data.textbook_id:
        result = await db.execute(select(Textbook).where(Textbook.id == data.textbook_id))
        if not result.scalar_one_or_none():
            raise HTTPException(400, f"Textbook {data.textbook_id} not found")

    if data.paragraph_id:
        result = await db.execute(select(Paragraph).where(Paragraph.id == data.paragraph_id))
        if not result.scalar_one_or_none():
            raise HTTPException(400, f"Paragraph {data.paragraph_id} not found")

    quest = DailyQuest(
        code=data.code,
        name_kk=data.name_kk,
        name_ru=data.name_ru,
        description_kk=data.description_kk,
        description_ru=data.description_ru,
        quest_type=qt,
        target_value=data.target_value,
        xp_reward=data.xp_reward,
        is_active=data.is_active,
        school_id=None,  # Global quest
        subject_id=data.subject_id,
        textbook_id=data.textbook_id,
        paragraph_id=data.paragraph_id,
    )

    repo = GamificationRepository(db)
    quest = await repo.create_daily_quest(quest)
    await db.commit()

    # Reload with relationships
    quest = await repo.get_daily_quest_by_id(quest.id)
    return _to_admin_response(quest)


@router.get("/{quest_id}", response_model=DailyQuestAdminResponse)
async def get_global_daily_quest(
    quest_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get a single global daily quest."""
    repo = GamificationRepository(db)
    quest = await repo.get_daily_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(404, "Daily quest not found")
    if quest.school_id is not None:
        raise HTTPException(403, "This quest belongs to a school, not global")
    return _to_admin_response(quest)


@router.put("/{quest_id}", response_model=DailyQuestAdminResponse)
async def update_global_daily_quest(
    quest_id: int,
    data: DailyQuestUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a global daily quest."""
    repo = GamificationRepository(db)
    quest = await repo.get_daily_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(404, "Daily quest not found")
    if quest.school_id is not None:
        raise HTTPException(403, "This quest belongs to a school, not global")

    update_data = data.model_dump(exclude_unset=True)

    # Validate quest_type if provided
    if 'quest_type' in update_data:
        try:
            update_data['quest_type'] = QuestType(update_data['quest_type'])
        except ValueError:
            raise HTTPException(400, f"Invalid quest_type: {update_data['quest_type']}")

    # Validate FK references if provided
    if 'subject_id' in update_data and update_data['subject_id']:
        from app.models.subject import Subject
        result = await db.execute(select(Subject).where(Subject.id == update_data['subject_id']))
        if not result.scalar_one_or_none():
            raise HTTPException(400, f"Subject {update_data['subject_id']} not found")

    if 'textbook_id' in update_data and update_data['textbook_id']:
        result = await db.execute(select(Textbook).where(Textbook.id == update_data['textbook_id']))
        if not result.scalar_one_or_none():
            raise HTTPException(400, f"Textbook {update_data['textbook_id']} not found")

    if 'paragraph_id' in update_data and update_data['paragraph_id']:
        result = await db.execute(select(Paragraph).where(Paragraph.id == update_data['paragraph_id']))
        if not result.scalar_one_or_none():
            raise HTTPException(400, f"Paragraph {update_data['paragraph_id']} not found")

    for key, value in update_data.items():
        setattr(quest, key, value)

    await repo.update_daily_quest(quest)
    await db.commit()

    quest = await repo.get_daily_quest_by_id(quest_id)
    return _to_admin_response(quest)


@router.delete("/{quest_id}")
async def delete_global_daily_quest(
    quest_id: int,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Deactivate a global daily quest."""
    repo = GamificationRepository(db)
    quest = await repo.get_daily_quest_by_id(quest_id)
    if not quest:
        raise HTTPException(404, "Daily quest not found")
    if quest.school_id is not None:
        raise HTTPException(403, "This quest belongs to a school, not global")

    await repo.delete_daily_quest(quest_id)
    await db.commit()
    return {"detail": "Quest deactivated"}
