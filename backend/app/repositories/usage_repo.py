"""
Repository for subscription plans, school subscriptions, and daily usage counters.
"""

import logging
from datetime import date
from typing import Optional, Dict, List

from sqlalchemy import select, func, text as sa_text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.subscription import SubscriptionPlan, SchoolSubscription, DailyUsageCounter

logger = logging.getLogger(__name__)


class UsageRepository:
    """Repository for usage tracking and subscription data access."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── Counter operations ──

    async def increment_counter(
        self,
        user_id: int,
        school_id: Optional[int],
        feature: str,
        tokens: int = 0,
    ) -> None:
        """
        UPSERT: increment message_count (+1) and token_count for today.
        Uses INSERT ... ON CONFLICT for atomicity.
        """
        sql = sa_text("""
            INSERT INTO daily_usage_counters (user_id, school_id, usage_date, feature, message_count, token_count)
            VALUES (:user_id, :school_id, CURRENT_DATE, :feature, 1, :tokens)
            ON CONFLICT (user_id, usage_date, feature)
            DO UPDATE SET
                message_count = daily_usage_counters.message_count + 1,
                token_count = daily_usage_counters.token_count + :tokens,
                updated_at = NOW()
        """)
        await self.db.execute(sql, {
            "user_id": user_id,
            "school_id": school_id,
            "feature": feature,
            "tokens": tokens,
        })

    async def get_user_daily_usage(
        self, user_id: int, usage_date: Optional[date] = None
    ) -> Dict[str, int]:
        """Get {feature: message_count} for a user on a given day (default: today)."""
        target_date = usage_date or date.today()
        result = await self.db.execute(
            select(DailyUsageCounter.feature, DailyUsageCounter.message_count)
            .where(
                DailyUsageCounter.user_id == user_id,
                DailyUsageCounter.usage_date == target_date,
            )
        )
        return {row.feature: row.message_count for row in result.fetchall()}

    async def get_school_daily_usage(
        self, school_id: int, usage_date: Optional[date] = None
    ) -> Dict[str, int]:
        """Get aggregated {feature: total_message_count} for all users in a school."""
        target_date = usage_date or date.today()
        result = await self.db.execute(
            select(
                DailyUsageCounter.feature,
                func.sum(DailyUsageCounter.message_count).label("total"),
            )
            .where(
                DailyUsageCounter.school_id == school_id,
                DailyUsageCounter.usage_date == target_date,
            )
            .group_by(DailyUsageCounter.feature)
        )
        return {row.feature: row.total for row in result.fetchall()}

    async def get_all_schools_daily_usage(
        self, usage_date: Optional[date] = None
    ) -> List[Dict]:
        """Get usage summary per school for admin overview."""
        target_date = usage_date or date.today()
        result = await self.db.execute(
            select(
                DailyUsageCounter.school_id,
                func.sum(DailyUsageCounter.message_count).label("total_messages"),
                func.sum(DailyUsageCounter.token_count).label("total_tokens"),
                func.count(func.distinct(DailyUsageCounter.user_id)).label("active_users"),
            )
            .where(DailyUsageCounter.usage_date == target_date)
            .group_by(DailyUsageCounter.school_id)
        )
        return [
            {
                "school_id": row.school_id,
                "total_messages": row.total_messages,
                "total_tokens": row.total_tokens,
                "active_users": row.active_users,
            }
            for row in result.fetchall()
        ]

    # ── Subscription operations ──

    async def get_active_subscription(self, school_id: int) -> Optional[SchoolSubscription]:
        """Get the active subscription for a school (with plan eager-loaded)."""
        result = await self.db.execute(
            select(SchoolSubscription).where(
                SchoolSubscription.school_id == school_id,
                SchoolSubscription.is_active == True,
            )
        )
        return result.scalar_one_or_none()

    async def get_default_plan(self) -> Optional[SubscriptionPlan]:
        """Get the 'free' plan as fallback."""
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.name == "free")
        )
        return result.scalar_one_or_none()

    async def get_plan_by_id(self, plan_id: int) -> Optional[SubscriptionPlan]:
        result = await self.db.execute(
            select(SubscriptionPlan).where(SubscriptionPlan.id == plan_id)
        )
        return result.scalar_one_or_none()

    async def list_plans(self, active_only: bool = True) -> List[SubscriptionPlan]:
        query = select(SubscriptionPlan).order_by(SubscriptionPlan.sort_order)
        if active_only:
            query = query.where(SubscriptionPlan.is_active == True)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def create_plan(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        self.db.add(plan)
        await self.db.flush()
        return plan

    async def update_plan(self, plan: SubscriptionPlan) -> SubscriptionPlan:
        await self.db.flush()
        return plan

    async def list_school_subscriptions(self) -> List[SchoolSubscription]:
        result = await self.db.execute(
            select(SchoolSubscription).order_by(SchoolSubscription.created_at.desc())
        )
        return list(result.scalars().all())

    async def create_school_subscription(
        self, subscription: SchoolSubscription
    ) -> SchoolSubscription:
        self.db.add(subscription)
        await self.db.flush()
        return subscription

    async def get_school_subscription_by_id(
        self, sub_id: int
    ) -> Optional[SchoolSubscription]:
        result = await self.db.execute(
            select(SchoolSubscription).where(SchoolSubscription.id == sub_id)
        )
        return result.scalar_one_or_none()

    async def deactivate_school_subscriptions(self, school_id: int) -> None:
        """Deactivate all active subscriptions for a school (before assigning new one)."""
        result = await self.db.execute(
            select(SchoolSubscription).where(
                SchoolSubscription.school_id == school_id,
                SchoolSubscription.is_active == True,
            )
        )
        for sub in result.scalars().all():
            sub.is_active = False
        await self.db.flush()
