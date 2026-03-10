"""
Service for managing subscription plans, usage counters, and limit checks.
"""

import logging
from datetime import date
from typing import Optional, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import SubscriptionPlan, SchoolSubscription, DailyUsageCounter
from app.repositories.usage_repo import UsageRepository
from app.schemas.subscription import (
    LimitCheckResult,
    FeatureUsageDetail,
    UsageSummaryResponse,
    SubscriptionPlanCreate,
    SubscriptionPlanUpdate,
    SchoolSubscriptionCreate,
)

logger = logging.getLogger(__name__)


class UsageLimitService:
    """Manages subscription plans, usage counting, and limit checking."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = UsageRepository(db)

    # ── Limit checking ──

    async def check_limit(
        self, user_id: int, school_id: Optional[int], feature: str
    ) -> LimitCheckResult:
        """
        Check if user can make another LLM request.
        SUPER_ADMIN (school_id=None) always allowed.
        """
        if school_id is None:
            return LimitCheckResult(
                allowed=True, feature=feature, current_count=0, limit=None, remaining=None
            )

        plan, overrides = await self._get_effective_plan(school_id)
        if plan is None:
            return LimitCheckResult(
                allowed=True, feature=feature, current_count=0, limit=None, remaining=None
            )

        # Get feature-specific limit
        feature_limit = self._get_feature_limit(plan, overrides, feature)
        if feature_limit is None:
            return LimitCheckResult(
                allowed=True, feature=feature, current_count=0, limit=None, remaining=None
            )

        # Get current count
        usage = await self.repo.get_user_daily_usage(user_id)
        current_count = usage.get(feature, 0)
        remaining = max(0, feature_limit - current_count)

        return LimitCheckResult(
            allowed=current_count < feature_limit,
            feature=feature,
            current_count=current_count,
            limit=feature_limit,
            remaining=remaining,
        )

    async def _get_effective_plan(
        self, school_id: int
    ) -> tuple[Optional[SubscriptionPlan], Optional[Dict[str, int]]]:
        """Get the active plan for a school with overrides. Falls back to 'free'."""
        subscription = await self.repo.get_active_subscription(school_id)
        if subscription:
            return subscription.plan, subscription.limit_overrides
        default = await self.repo.get_default_plan()
        return default, None

    def _get_feature_limit(
        self,
        plan: SubscriptionPlan,
        overrides: Optional[Dict[str, int]],
        feature: str,
    ) -> Optional[int]:
        """Get limit for a specific feature, considering overrides."""
        # Check overrides first
        if overrides and feature in overrides:
            return overrides[feature]
        # Check plan feature_limits
        feature_limits = plan.feature_limits or {}
        if feature in feature_limits:
            return feature_limits[feature]
        # Fall back to daily_message_limit (global cap)
        return plan.daily_message_limit

    # ── Usage counting ──

    async def increment_usage(
        self,
        user_id: Optional[int],
        school_id: Optional[int],
        feature: str,
        tokens: int = 0,
    ) -> None:
        """Increment the daily counter for a user. Called after successful LLM call."""
        if user_id is None:
            return
        try:
            await self.repo.increment_counter(user_id, school_id, feature, tokens)
        except Exception as e:
            logger.warning(f"Failed to increment usage counter: {e}")

    # ── Usage summaries ──

    async def get_user_summary(
        self, user_id: int, school_id: Optional[int], usage_date: Optional[date] = None
    ) -> UsageSummaryResponse:
        """Get full usage summary for a user with plan limits."""
        target_date = usage_date or date.today()
        usage = await self.repo.get_user_daily_usage(user_id, target_date)

        plan = None
        overrides = None
        if school_id:
            plan, overrides = await self._get_effective_plan(school_id)

        features = []
        all_features = ["chat", "rag", "teacher_chat", "lesson_plan"]
        for feat in all_features:
            used = usage.get(feat, 0)
            limit = self._get_feature_limit(plan, overrides, feat) if plan else None
            remaining = max(0, limit - used) if limit is not None else None
            features.append(FeatureUsageDetail(
                feature=feat, used=used, limit=limit, remaining=remaining
            ))

        total_used = sum(usage.values())
        daily_limit = plan.daily_message_limit if plan else None
        daily_remaining = max(0, daily_limit - total_used) if daily_limit is not None else None

        return UsageSummaryResponse(
            user_id=user_id,
            usage_date=target_date,
            plan_name=plan.name if plan else None,
            plan_display_name=plan.display_name if plan else None,
            features=features,
            total_used=total_used,
            daily_limit=daily_limit,
            daily_remaining=daily_remaining,
        )

    # ── Plan CRUD ──

    async def list_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        return await self.repo.list_plans(active_only)

    async def create_plan(self, data: SubscriptionPlanCreate) -> SubscriptionPlan:
        plan = SubscriptionPlan(
            name=data.name,
            display_name=data.display_name,
            daily_message_limit=data.daily_message_limit,
            feature_limits=data.feature_limits,
            description=data.description,
            sort_order=data.sort_order,
            price_monthly_kzt=data.price_monthly_kzt,
            price_yearly_kzt=data.price_yearly_kzt,
        )
        return await self.repo.create_plan(plan)

    async def update_plan(self, plan_id: int, data: SubscriptionPlanUpdate) -> Optional[SubscriptionPlan]:
        plan = await self.repo.get_plan_by_id(plan_id)
        if not plan:
            return None
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(plan, field, value)
        return await self.repo.update_plan(plan)

    # ── Subscription CRUD ──

    async def list_school_subscriptions(self) -> List[SchoolSubscription]:
        return await self.repo.list_school_subscriptions()

    async def assign_plan_to_school(
        self, data: SchoolSubscriptionCreate, activated_by: int
    ) -> SchoolSubscription:
        """Assign a plan to a school. Deactivates any existing active subscription."""
        await self.repo.deactivate_school_subscriptions(data.school_id)
        sub = SchoolSubscription(
            school_id=data.school_id,
            plan_id=data.plan_id,
            expires_at=data.expires_at,
            limit_overrides=data.limit_overrides,
            notes=data.notes,
            is_active=True,
            activated_by=activated_by,
        )
        return await self.repo.create_school_subscription(sub)

    async def update_school_subscription(
        self, sub_id: int, data: dict
    ) -> Optional[SchoolSubscription]:
        sub = await self.repo.get_school_subscription_by_id(sub_id)
        if not sub:
            return None
        for field, value in data.items():
            if value is not None:
                setattr(sub, field, value)
        await self.db.flush()
        return sub

    async def get_all_schools_usage(self, usage_date: Optional[date] = None) -> List[Dict]:
        return await self.repo.get_all_schools_daily_usage(usage_date)
