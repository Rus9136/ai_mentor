"""
Schemas for subscription plans, school subscriptions, and usage counters.
"""

from datetime import datetime, date
from typing import Optional, Dict, List

from pydantic import BaseModel, ConfigDict


# ── Subscription Plans ──

class SubscriptionPlanCreate(BaseModel):
    name: str
    display_name: str
    daily_message_limit: Optional[int] = None
    feature_limits: Dict[str, int] = {}
    description: Optional[str] = None
    sort_order: int = 0
    price_monthly_kzt: Optional[int] = None
    price_yearly_kzt: Optional[int] = None


class SubscriptionPlanUpdate(BaseModel):
    display_name: Optional[str] = None
    daily_message_limit: Optional[int] = None
    feature_limits: Optional[Dict[str, int]] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    price_monthly_kzt: Optional[int] = None
    price_yearly_kzt: Optional[int] = None


class SubscriptionPlanResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    display_name: str
    daily_message_limit: Optional[int] = None
    feature_limits: Dict[str, int] = {}
    is_active: bool
    sort_order: int
    description: Optional[str] = None
    price_monthly_kzt: Optional[int] = None
    price_yearly_kzt: Optional[int] = None
    created_at: datetime
    updated_at: datetime


# ── School Subscriptions ──

class SchoolSubscriptionCreate(BaseModel):
    school_id: int
    plan_id: int
    expires_at: Optional[datetime] = None
    limit_overrides: Optional[Dict[str, int]] = None
    notes: Optional[str] = None


class SchoolSubscriptionUpdate(BaseModel):
    plan_id: Optional[int] = None
    expires_at: Optional[datetime] = None
    limit_overrides: Optional[Dict[str, int]] = None
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class SchoolSubscriptionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    school_id: int
    plan_id: int
    plan: Optional[SubscriptionPlanResponse] = None
    starts_at: datetime
    expires_at: Optional[datetime] = None
    limit_overrides: Optional[Dict[str, int]] = None
    is_active: bool
    activated_by: Optional[int] = None
    notes: Optional[str] = None
    created_at: datetime


# ── Usage Counters ──

class DailyUsageResponse(BaseModel):
    """Usage counters for a user on a given day."""
    user_id: int
    usage_date: date
    counters: Dict[str, int]  # feature -> message_count
    total_messages: int


class FeatureUsageDetail(BaseModel):
    """Per-feature usage with limit info."""
    feature: str
    used: int
    limit: Optional[int] = None  # None = unlimited
    remaining: Optional[int] = None


class UsageSummaryResponse(BaseModel):
    """Full usage summary for a user today, including plan limits."""
    user_id: int
    usage_date: date
    plan_name: Optional[str] = None
    plan_display_name: Optional[str] = None
    features: List[FeatureUsageDetail]
    total_used: int
    daily_limit: Optional[int] = None
    daily_remaining: Optional[int] = None


class LimitCheckResult(BaseModel):
    """Result of a rate limit check."""
    allowed: bool
    feature: str
    current_count: int
    limit: Optional[int] = None
    remaining: Optional[int] = None
