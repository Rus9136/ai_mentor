"""
Database configuration and session management.

This module provides:
- SQLAlchemy async engine configuration
- Session factory with automatic RLS context setup
- get_db() dependency that sets session variables from tenant context
"""
from typing import AsyncGenerator
import logging
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import text

from app.core.config import settings
from app.core.tenant_context import get_tenant_context

logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.async_database_url,
    echo=settings.DEBUG,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


# Create declarative base
class Base(DeclarativeBase):
    """Base class for all models."""
    __allow_unmapped__ = True


async def _set_session_variables(session: AsyncSession) -> bool:
    """
    Set PostgreSQL session variables for RLS based on tenant context.

    This is the SINGLE place where session variables are set.
    Called automatically by get_db() for every database session.

    Args:
        session: Database session to configure

    Returns:
        True if context was set (authenticated), False otherwise

    Session variables set:
        - app.current_user_id: Current user's ID
        - app.current_tenant_id: School ID (or NULL for super_admin)
        - app.is_super_admin: 'true' or 'false'
    """
    ctx = get_tenant_context()

    if not ctx.is_authenticated:
        # Unauthenticated request - clear all context
        # RLS policies will deny access to protected resources
        # NOTE: Using false for is_local so variables persist across transactions
        await session.execute(
            text("SELECT set_config('app.current_user_id', NULL, false)")
        )
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', NULL, false)")
        )
        await session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', false)")
        )
        logger.debug("RLS context: unauthenticated (all NULL)")
        return False

    # Set current user ID
    # NOTE: Using false for is_local so variables persist across commit() calls
    await session.execute(
        text("SELECT set_config('app.current_user_id', :user_id, false)"),
        {"user_id": str(ctx.user_id)}
    )

    # Set super admin flag
    is_super_admin = ctx.is_super_admin
    await session.execute(
        text("SELECT set_config('app.is_super_admin', :value, false)"),
        {"value": "true" if is_super_admin else "false"}
    )

    # Set tenant ID (school_id)
    if is_super_admin:
        # Super admin bypasses RLS - set NULL tenant
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', NULL, false)")
        )
        logger.debug(
            f"RLS context: SUPER_ADMIN user_id={ctx.user_id} (tenant=NULL)"
        )
    elif ctx.school_id is not None:
        # Regular user with school - set tenant
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', :tenant_id, false)"),
            {"tenant_id": str(ctx.school_id)}
        )
        logger.debug(
            f"RLS context: user_id={ctx.user_id}, school_id={ctx.school_id}"
        )
    else:
        # User without school (e.g., during onboarding) - set NULL tenant
        await session.execute(
            text("SELECT set_config('app.current_tenant_id', NULL, false)")
        )
        logger.debug(
            f"RLS context: user_id={ctx.user_id}, no school (tenant=NULL)"
        )

    return True


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting async database session with RLS context.

    This is the ONLY way to get a database session. It automatically:
    1. Creates a new session from the connection pool
    2. Reads tenant context from contextvars (set by TenancyMiddleware)
    3. Sets PostgreSQL session variables for RLS policies
    4. Yields the configured session
    5. Commits on success, rollbacks on error

    Usage in endpoints:
        @router.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            # RLS is already configured - queries are automatically filtered
            result = await db.execute(select(Item))
            return result.scalars().all()

    Yields:
        AsyncSession: Database session with RLS context configured
    """
    async with AsyncSessionLocal() as session:
        try:
            # Set RLS session variables from tenant context
            await _set_session_variables(session)

            yield session

            # Commit if no errors
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_db_no_rls() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session WITHOUT RLS context.

    Use ONLY for operations that need to bypass RLS:
    - Authentication (login, refresh token)
    - User lookup during token validation
    - System operations

    WARNING: Data from this session is NOT filtered by school_id!
    Use with extreme caution.

    Yields:
        AsyncSession: Database session without RLS filtering
    """
    async with AsyncSessionLocal() as session:
        try:
            # Explicitly clear context to ensure no RLS filtering
            # NOTE: Using false for is_local for consistency across commits
            await session.execute(
                text("SELECT set_config('app.current_user_id', NULL, false)")
            )
            await session.execute(
                text("SELECT set_config('app.current_tenant_id', NULL, false)")
            )
            await session.execute(
                text("SELECT set_config('app.is_super_admin', 'false', false)")
            )

            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def verify_rls_context(session: AsyncSession) -> dict:
    """
    Verify that RLS session variables are properly set.

    Use for debugging and testing RLS configuration.

    Args:
        session: Database session to check

    Returns:
        Dict with current session variable values

    Example:
        ctx = await verify_rls_context(db)
        assert ctx["user_id"] == expected_user_id
        assert ctx["tenant_id"] == expected_school_id
    """
    result = {}

    # Get current_user_id
    row = await session.execute(
        text("SELECT current_setting('app.current_user_id', true)")
    )
    value = row.scalar()
    result["user_id"] = int(value) if value and value != "" else None

    # Get current_tenant_id
    row = await session.execute(
        text("SELECT current_setting('app.current_tenant_id', true)")
    )
    value = row.scalar()
    result["tenant_id"] = int(value) if value and value != "" else None

    # Get is_super_admin
    row = await session.execute(
        text("SELECT current_setting('app.is_super_admin', true)")
    )
    value = row.scalar()
    result["is_super_admin"] = value == "true" if value else False

    return result
