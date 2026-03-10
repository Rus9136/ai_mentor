"""
Subscription and usage tracking models for SaaS rate limiting.
"""

from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    Index,
    func,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class SubscriptionPlan(BaseModel):
    """Defines a subscription tier with usage limits."""

    __tablename__ = "subscription_plans"

    name = Column(String(50), nullable=False, unique=True)
    display_name = Column(String(100), nullable=False)
    daily_message_limit = Column(Integer, nullable=True)  # NULL = unlimited
    feature_limits = Column(JSONB, nullable=False, server_default="{}")
    is_active = Column(Boolean, nullable=False, default=True)
    sort_order = Column(Integer, nullable=False, default=0)
    description = Column(Text, nullable=True)
    price_monthly_kzt = Column(Integer, nullable=True)
    price_yearly_kzt = Column(Integer, nullable=True)


class SchoolSubscription(BaseModel):
    """Links a school to a subscription plan."""

    __tablename__ = "school_subscriptions"

    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=False)
    plan_id = Column(Integer, ForeignKey("subscription_plans.id", ondelete="RESTRICT"), nullable=False)
    starts_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    limit_overrides = Column(JSONB, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True)
    activated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    plan = relationship("SubscriptionPlan", lazy="joined")
    school = relationship("School", lazy="joined")


class DailyUsageCounter(BaseModel):
    """Fast daily counter per user per feature for rate limiting."""

    __tablename__ = "daily_usage_counters"

    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    school_id = Column(Integer, ForeignKey("schools.id", ondelete="CASCADE"), nullable=True)
    usage_date = Column(Date, nullable=False)
    feature = Column(String(30), nullable=False)
    message_count = Column(Integer, nullable=False, default=0)
    token_count = Column(Integer, nullable=False, default=0)

    __table_args__ = (
        UniqueConstraint("user_id", "usage_date", "feature", name="uq_daily_usage_user_date_feature"),
        Index("ix_daily_usage_school_date", "school_id", "usage_date"),
        Index("ix_daily_usage_user_date", "user_id", "usage_date"),
    )
