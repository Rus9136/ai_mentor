"""
LLM Usage monitoring endpoints for SUPER_ADMIN.
"""
from datetime import date, datetime, timedelta
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select, func, case, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies import require_super_admin
from app.models.user import User
from app.models.llm_usage_log import LLMUsageLog
from sqlalchemy.orm import aliased
from app.schemas.llm_usage import (
    FeatureBreakdown,
    LLMUsageDailyStats,
    LLMUsageSchoolBreakdown,
    LLMUsageSummary,
    LLMUsageUserBreakdown,
    ModelBreakdown,
)

router = APIRouter(prefix="/llm-usage", tags=["LLM Usage (Global)"])


def _default_date_range(
    date_from: Optional[date],
    date_to: Optional[date],
) -> tuple[datetime, datetime]:
    """Default to last 30 days if not specified."""
    if not date_to:
        date_to = date.today()
    if not date_from:
        date_from = date_to - timedelta(days=30)
    return (
        datetime.combine(date_from, datetime.min.time()),
        datetime.combine(date_to, datetime.max.time()),
    )


@router.get("/stats", response_model=LLMUsageSummary)
async def get_global_stats(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get global LLM usage summary."""
    dt_from, dt_to = _default_date_range(date_from, date_to)

    base = select(LLMUsageLog).where(
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
    )

    # Aggregate totals
    totals_q = select(
        func.count().label("total_calls"),
        func.sum(case((LLMUsageLog.success == True, 1), else_=0)).label("successful"),
        func.sum(case((LLMUsageLog.success == False, 1), else_=0)).label("failed"),
        func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(LLMUsageLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(LLMUsageLog.completion_tokens), 0).label("completion_tokens"),
        func.avg(LLMUsageLog.latency_ms).label("avg_latency"),
    ).where(
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
    )
    row = (await db.execute(totals_q)).one()

    # By feature
    feat_q = select(
        LLMUsageLog.feature,
        func.count().label("total_calls"),
        func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(LLMUsageLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(LLMUsageLog.completion_tokens), 0).label("completion_tokens"),
        func.avg(LLMUsageLog.latency_ms).label("avg_latency"),
        func.sum(case((LLMUsageLog.success == False, 1), else_=0)).label("error_count"),
    ).where(
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
    ).group_by(LLMUsageLog.feature)

    feat_rows = (await db.execute(feat_q)).all()
    by_feature = [
        FeatureBreakdown(
            feature=r.feature.value if hasattr(r.feature, 'value') else str(r.feature),
            total_calls=r.total_calls,
            total_tokens=r.total_tokens,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            avg_latency_ms=int(r.avg_latency) if r.avg_latency else None,
            error_count=r.error_count,
        )
        for r in feat_rows
    ]

    # By model
    model_q = select(
        LLMUsageLog.model,
        LLMUsageLog.provider,
        func.count().label("total_calls"),
        func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
    ).where(
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
    ).group_by(LLMUsageLog.model, LLMUsageLog.provider)

    model_rows = (await db.execute(model_q)).all()
    by_model = [
        ModelBreakdown(
            model=r.model,
            provider=r.provider,
            total_calls=r.total_calls,
            total_tokens=r.total_tokens,
        )
        for r in model_rows
    ]

    return LLMUsageSummary(
        total_calls=row.total_calls,
        successful_calls=row.successful or 0,
        failed_calls=row.failed or 0,
        total_tokens=row.total_tokens,
        total_prompt_tokens=row.prompt_tokens,
        total_completion_tokens=row.completion_tokens,
        avg_latency_ms=int(row.avg_latency) if row.avg_latency else None,
        by_feature=by_feature,
        by_model=by_model,
    )


@router.get("/daily", response_model=List[LLMUsageDailyStats])
async def get_daily_stats(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get daily LLM usage breakdown."""
    dt_from, dt_to = _default_date_range(date_from, date_to)

    q = select(
        cast(LLMUsageLog.created_at, Date).label("day"),
        func.count().label("total_calls"),
        func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
        func.coalesce(func.sum(LLMUsageLog.prompt_tokens), 0).label("prompt_tokens"),
        func.coalesce(func.sum(LLMUsageLog.completion_tokens), 0).label("completion_tokens"),
        func.sum(case((LLMUsageLog.success == False, 1), else_=0)).label("error_count"),
    ).where(
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
    ).group_by("day").order_by("day")

    rows = (await db.execute(q)).all()
    return [
        LLMUsageDailyStats(
            date=r.day,
            total_calls=r.total_calls,
            total_tokens=r.total_tokens,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
            error_count=r.error_count,
        )
        for r in rows
    ]


@router.get("/by-school", response_model=List[LLMUsageSchoolBreakdown])
async def get_by_school(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get LLM usage breakdown by school."""
    dt_from, dt_to = _default_date_range(date_from, date_to)

    q = select(
        LLMUsageLog.school_id,
        func.count().label("total_calls"),
        func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
    ).where(
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
    ).group_by(LLMUsageLog.school_id).order_by(func.sum(LLMUsageLog.total_tokens).desc())

    rows = (await db.execute(q)).all()
    return [
        LLMUsageSchoolBreakdown(
            school_id=r.school_id,
            total_calls=r.total_calls,
            total_tokens=r.total_tokens,
        )
        for r in rows
    ]


@router.get("/by-user", response_model=List[LLMUsageUserBreakdown])
async def get_by_user(
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    school_id: Optional[int] = Query(None, description="Filter by school"),
    current_user: User = Depends(require_super_admin),
    db: AsyncSession = Depends(get_db),
):
    """Get LLM usage breakdown by user (global)."""
    dt_from, dt_to = _default_date_range(date_from, date_to)

    UserAlias = aliased(User)

    filters = [
        LLMUsageLog.created_at >= dt_from,
        LLMUsageLog.created_at <= dt_to,
        LLMUsageLog.user_id.isnot(None),
    ]
    if school_id is not None:
        filters.append(LLMUsageLog.school_id == school_id)

    q = (
        select(
            LLMUsageLog.user_id,
            LLMUsageLog.student_id,
            LLMUsageLog.teacher_id,
            LLMUsageLog.school_id,
            func.count().label("total_calls"),
            func.coalesce(func.sum(LLMUsageLog.total_tokens), 0).label("total_tokens"),
            func.coalesce(func.sum(LLMUsageLog.prompt_tokens), 0).label("prompt_tokens"),
            func.coalesce(func.sum(LLMUsageLog.completion_tokens), 0).label("completion_tokens"),
            UserAlias.first_name,
            UserAlias.last_name,
            UserAlias.email,
            UserAlias.role,
        )
        .outerjoin(UserAlias, LLMUsageLog.user_id == UserAlias.id)
        .where(*filters)
        .group_by(
            LLMUsageLog.user_id,
            LLMUsageLog.student_id,
            LLMUsageLog.teacher_id,
            LLMUsageLog.school_id,
            UserAlias.first_name,
            UserAlias.last_name,
            UserAlias.email,
            UserAlias.role,
        )
        .order_by(func.sum(LLMUsageLog.total_tokens).desc())
        .limit(100)
    )

    rows = (await db.execute(q)).all()
    return [
        LLMUsageUserBreakdown(
            user_id=r.user_id,
            student_id=r.student_id,
            teacher_id=r.teacher_id,
            user_name=f"{r.last_name} {r.first_name}" if r.last_name else None,
            user_email=r.email,
            user_role=r.role.value if hasattr(r.role, 'value') else str(r.role) if r.role else None,
            school_id=r.school_id,
            total_calls=r.total_calls,
            total_tokens=r.total_tokens,
            prompt_tokens=r.prompt_tokens,
            completion_tokens=r.completion_tokens,
        )
        for r in rows
    ]
