"""
Subscription management endpoints for SUPER_ADMIN.
"""

from datetime import date
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.services.usage_limit_service import UsageLimitService
from app.schemas.subscription import (
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SubscriptionPlanResponse,
    SchoolSubscriptionCreate,
    SchoolSubscriptionUpdate,
    SchoolSubscriptionResponse,
    UsageSummaryResponse,
)

router = APIRouter(prefix="/subscriptions", tags=["Subscriptions (Global)"])


# ── Plans CRUD ──

@router.get("/plans", response_model=List[SubscriptionPlanResponse])
async def list_plans(
    active_only: bool = Query(True),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all subscription plans."""
    service = UsageLimitService(db)
    plans = await service.list_plans(active_only=active_only)
    return plans


@router.post("/plans", response_model=SubscriptionPlanResponse)
async def create_plan(
    data: SubscriptionPlanCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Create a new subscription plan."""
    service = UsageLimitService(db)
    plan = await service.create_plan(data)
    await db.commit()
    return plan


@router.put("/plans/{plan_id}", response_model=SubscriptionPlanResponse)
async def update_plan(
    plan_id: int,
    data: SubscriptionPlanUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update an existing subscription plan."""
    service = UsageLimitService(db)
    plan = await service.update_plan(plan_id, data)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    await db.commit()
    return plan


# ── School Subscriptions ──

@router.get("/schools", response_model=List[SchoolSubscriptionResponse])
async def list_school_subscriptions(
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """List all school subscriptions."""
    service = UsageLimitService(db)
    subs = await service.list_school_subscriptions()
    return subs


@router.post("/schools", response_model=SchoolSubscriptionResponse)
async def assign_plan_to_school(
    data: SchoolSubscriptionCreate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Assign a subscription plan to a school. Deactivates any existing subscription."""
    service = UsageLimitService(db)
    sub = await service.assign_plan_to_school(data, activated_by=current_user.id)
    await db.commit()
    return sub


@router.put("/schools/{sub_id}", response_model=SchoolSubscriptionResponse)
async def update_school_subscription(
    sub_id: int,
    data: SchoolSubscriptionUpdate,
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Update a school subscription."""
    service = UsageLimitService(db)
    update_data = data.model_dump(exclude_unset=True)
    sub = await service.update_school_subscription(sub_id, update_data)
    if not sub:
        raise HTTPException(status_code=404, detail="Subscription not found")
    await db.commit()
    return sub


# ── Usage Overview ──

@router.get("/usage")
async def get_usage_overview(
    usage_date: Optional[date] = Query(None, description="Date to check (default: today)"),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get daily usage overview for all schools."""
    service = UsageLimitService(db)
    usage = await service.get_all_schools_usage(usage_date)
    return {"date": (usage_date or date.today()).isoformat(), "schools": usage}


@router.get("/usage/{school_id}", response_model=UsageSummaryResponse)
async def get_school_usage_detail(
    school_id: int,
    usage_date: Optional[date] = Query(None),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get detailed usage for a specific school (aggregated across users)."""
    # Use a representative query — for school-level view, we show aggregated data
    service = UsageLimitService(db)
    # Get school's plan info using a dummy user_id=0 call for plan details
    from app.repositories.usage_repo import UsageRepository
    repo = UsageRepository(db)
    school_usage = await repo.get_school_daily_usage(school_id, usage_date)

    plan, overrides = await service._get_effective_plan(school_id)
    features = []
    for feat in ["chat", "rag", "teacher_chat", "lesson_plan"]:
        used = school_usage.get(feat, 0)
        limit = service._get_feature_limit(plan, overrides, feat) if plan else None
        features.append({
            "feature": feat,
            "used": used,
            "limit": limit,
            "remaining": max(0, limit - used) if limit is not None else None,
        })

    total_used = sum(school_usage.values())
    daily_limit = plan.daily_message_limit if plan else None

    return UsageSummaryResponse(
        user_id=0,  # school-level aggregate
        usage_date=usage_date or date.today(),
        plan_name=plan.name if plan else None,
        plan_display_name=plan.display_name if plan else None,
        features=[
            {"feature": f["feature"], "used": f["used"], "limit": f["limit"], "remaining": f["remaining"]}
            for f in features
        ],
        total_used=total_used,
        daily_limit=daily_limit,
        daily_remaining=max(0, daily_limit - total_used) if daily_limit is not None else None,
    )
