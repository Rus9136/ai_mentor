"""
Schemas for LLM usage monitoring API.
"""
from datetime import datetime, date
from typing import Optional, List

from pydantic import BaseModel, ConfigDict


class LLMUsageLogResponse(BaseModel):
    """Single LLM usage log entry."""
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: Optional[int] = None
    school_id: Optional[int] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    feature: str
    provider: str
    model: str
    prompt_tokens: Optional[int] = None
    completion_tokens: Optional[int] = None
    total_tokens: Optional[int] = None
    latency_ms: Optional[int] = None
    success: bool
    error_message: Optional[str] = None
    estimated_cost_usd: Optional[float] = None
    created_at: datetime


class FeatureBreakdown(BaseModel):
    """Token usage breakdown by feature."""
    feature: str
    total_calls: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    avg_latency_ms: Optional[int] = None
    error_count: int = 0


class ModelBreakdown(BaseModel):
    """Token usage breakdown by model."""
    model: str
    provider: str
    total_calls: int
    total_tokens: int


class LLMUsageSummary(BaseModel):
    """Aggregated LLM usage summary."""
    total_calls: int
    successful_calls: int
    failed_calls: int
    total_tokens: int
    total_prompt_tokens: int
    total_completion_tokens: int
    avg_latency_ms: Optional[int] = None
    by_feature: List[FeatureBreakdown]
    by_model: List[ModelBreakdown]


class LLMUsageDailyStats(BaseModel):
    """Daily LLM usage statistics."""
    date: date
    total_calls: int
    total_tokens: int
    prompt_tokens: int
    completion_tokens: int
    error_count: int = 0


class LLMUsageUserBreakdown(BaseModel):
    """LLM usage breakdown by user (for school admin)."""
    user_id: Optional[int] = None
    student_id: Optional[int] = None
    teacher_id: Optional[int] = None
    total_calls: int
    total_tokens: int


class LLMUsageSchoolBreakdown(BaseModel):
    """LLM usage breakdown by school (for super admin)."""
    school_id: Optional[int] = None
    total_calls: int
    total_tokens: int
