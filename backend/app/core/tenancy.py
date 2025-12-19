"""
Tenancy management for multi-tenant architecture.

Manages PostgreSQL session variables for Row Level Security (RLS) isolation.
Each request sets the current tenant (school_id) via session variable,
which is then used by RLS policies to automatically filter data.
"""
from typing import Optional
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession


async def set_current_tenant(db: AsyncSession, school_id: int) -> None:
    """
    Set current tenant (school_id) for RLS policies.

    Sets PostgreSQL session variable 'app.current_tenant_id' which is used
    by Row Level Security policies to automatically filter data.

    Args:
        db: Database session
        school_id: ID of the school (tenant)

    Example:
        await set_current_tenant(db, 1)
        # All subsequent queries in this session will be filtered by school_id = 1
    """
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
        {"tenant_id": str(school_id)}
    )


async def get_current_tenant(db: AsyncSession) -> Optional[int]:
    """
    Get current tenant (school_id) from session variable.

    Reads PostgreSQL session variable 'app.current_tenant_id'.

    Args:
        db: Database session

    Returns:
        Current tenant ID if set, None otherwise

    Example:
        tenant_id = await get_current_tenant(db)
        if tenant_id:
            print(f"Current tenant: {tenant_id}")
    """
    result = await db.execute(
        text("SELECT current_setting('app.current_tenant_id', true)")
    )
    value = result.scalar()

    if value and value != '':
        return int(value)
    return None


async def reset_tenant(db: AsyncSession) -> None:
    """
    Reset tenant context (clear session variable).

    Used for SUPER_ADMIN users who should see all data (bypass RLS).
    Also used to clean up context between requests.

    Args:
        db: Database session

    Example:
        await reset_tenant(db)
        # All subsequent queries will not be filtered by tenant
    """
    # Use NULL instead of empty string to avoid casting errors in RLS policies
    await db.execute(
        text("SELECT set_config('app.current_tenant_id', NULL, false)")
    )


async def set_super_admin_flag(db: AsyncSession, is_super_admin: bool) -> None:
    """
    Set SUPER_ADMIN flag in session variable.

    Optional: Used if we implement SUPER_ADMIN bypass through RLS policies
    instead of database role BYPASSRLS.

    Args:
        db: Database session
        is_super_admin: Whether current user is SUPER_ADMIN

    Example:
        await set_super_admin_flag(db, True)
    """
    await db.execute(
        text("SELECT set_config('app.is_super_admin', :value, false)"),
        {"value": "true" if is_super_admin else "false"}
    )


async def set_current_user_id(db: AsyncSession, user_id: int) -> None:
    """
    Set current user ID for RLS policies.

    Used by RLS policies to allow users to update their own records.

    Args:
        db: Database session
        user_id: ID of the current user

    Example:
        await set_current_user_id(db, 123)
    """
    await db.execute(
        text("SELECT set_config('app.current_user_id', :user_id, false)"),
        {"user_id": str(user_id)}
    )
