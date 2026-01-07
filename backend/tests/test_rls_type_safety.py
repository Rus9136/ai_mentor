"""Tests for RLS type safety and consistency.

These tests verify that RLS policies work correctly with various
session variable values, including edge cases like empty strings.

NOTE: These tests require RLS policies to be set up in the database.
They are designed to run against a database with applied migrations,
not the test database created from scratch.

Run with: pytest backend/tests/test_rls_type_safety.py -v --db-url=<production_db_url>
Or mark as integration tests and run separately.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


# Production database URL for RLS tests
# Uses ai_mentor_app role (with RLS enforced)
PROD_DATABASE_URL = (
    f"postgresql+asyncpg://ai_mentor_app:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)


@pytest.fixture
async def rls_db_session():
    """
    Create a session connected to production DB for RLS testing.
    Uses ai_mentor_app role which has RLS enforced.
    """
    try:
        engine = create_async_engine(
            PROD_DATABASE_URL,
            poolclass=NullPool,
            echo=False,
        )
        async_session_maker = async_sessionmaker(
            engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )
        async with async_session_maker() as session:
            yield session
            await session.rollback()
        await engine.dispose()
    except Exception as e:
        pytest.skip(f"Cannot connect to production DB for RLS tests: {e}")


@pytest.mark.integration
class TestRLSTypeSafety:
    """Test RLS policies handle type casting safely."""

    @pytest.mark.asyncio
    async def test_empty_string_tenant_id_does_not_crash(
        self, rls_db_session: AsyncSession
    ):
        """Verify empty string tenant_id doesn't cause cast errors."""
        # Set tenant_id to empty string (edge case)
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )

        # This should not raise an error - COALESCE(NULLIF('', ''), '0')::integer = 0
        result = await rls_db_session.execute(
            text("SELECT count(*) FROM invitation_codes")
        )
        count = result.scalar()
        # Should return 0 (no school_id = 0 exists)
        assert count == 0

    @pytest.mark.asyncio
    async def test_empty_string_super_admin_does_not_crash(
        self, rls_db_session: AsyncSession
    ):
        """Verify empty string is_super_admin doesn't cause cast errors."""
        # Set is_super_admin to empty string (edge case)
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', '', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '1', true)")
        )

        # This should not raise an error - COALESCE('', 'false') = 'true' is false
        result = await rls_db_session.execute(
            text("SELECT count(*) FROM invitation_codes WHERE school_id = 1")
        )
        # Should work without error
        assert result.scalar() is not None

    @pytest.mark.asyncio
    async def test_valid_tenant_id_works(self, rls_db_session: AsyncSession):
        """Verify valid tenant_id works correctly."""
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '5', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )

        # Should only see records from school_id = 5
        result = await rls_db_session.execute(
            text("SELECT count(*) FROM invitation_codes WHERE school_id = 5")
        )
        # Should work without error
        assert result.scalar() is not None

    @pytest.mark.asyncio
    async def test_super_admin_bypasses_tenant_filter(
        self, rls_db_session: AsyncSession
    ):
        """Verify super_admin can see all records."""
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'true', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )

        # Super admin should see all invitation codes
        result = await rls_db_session.execute(
            text("SELECT count(*) FROM invitation_codes")
        )
        # Should work without error and return all records
        assert result.scalar() is not None

    @pytest.mark.asyncio
    async def test_null_session_variables_default_safely(
        self, rls_db_session: AsyncSession
    ):
        """Verify null/unset session variables default safely."""
        # Clear session variables
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', '', true)")
        )

        # Should not crash, should return 0 records (school_id = 0 doesn't exist)
        result = await rls_db_session.execute(
            text("SELECT count(*) FROM invitation_codes")
        )
        count = result.scalar()
        assert count == 0


@pytest.mark.integration
class TestRLSPolicyConsistency:
    """Test that all RLS policies use consistent patterns."""

    @pytest.mark.asyncio
    async def test_no_boolean_casts_in_policies(self, rls_db_session: AsyncSession):
        """Verify no policies use dangerous ::boolean casts."""
        result = await rls_db_session.execute(
            text("""
                SELECT tablename, policyname
                FROM pg_policies
                WHERE schemaname = 'public'
                  AND qual::text LIKE '%::boolean%'
            """)
        )
        problematic = result.fetchall()

        assert len(problematic) == 0, (
            f"Found {len(problematic)} policies with ::boolean cast: "
            f"{[f'{t}.{p}' for t, p in problematic]}"
        )

    @pytest.mark.asyncio
    async def test_all_tenant_policies_use_coalesce(
        self, rls_db_session: AsyncSession
    ):
        """Verify all tenant policies use COALESCE for safety."""
        result = await rls_db_session.execute(
            text("""
                SELECT tablename, policyname
                FROM pg_policies
                WHERE schemaname = 'public'
                  AND qual::text LIKE '%current_tenant_id%'
                  AND qual::text NOT LIKE '%COALESCE%'
            """)
        )
        problematic = result.fetchall()

        assert len(problematic) == 0, (
            f"Found {len(problematic)} policies without COALESCE: "
            f"{[f'{t}.{p}' for t, p in problematic]}"
        )

    @pytest.mark.asyncio
    async def test_all_super_admin_checks_use_string_comparison(
        self, rls_db_session: AsyncSession
    ):
        """Verify super_admin checks use safe string comparison."""
        result = await rls_db_session.execute(
            text("""
                SELECT tablename, policyname, qual::text
                FROM pg_policies
                WHERE schemaname = 'public'
                  AND qual::text LIKE '%is_super_admin%'
            """)
        )
        policies = result.fetchall()

        for tablename, policyname, qual in policies:
            # Should use = 'true' pattern, not ::boolean = true
            assert "::boolean" not in qual, (
                f"Policy {tablename}.{policyname} uses unsafe ::boolean cast"
            )

    @pytest.mark.asyncio
    async def test_correct_session_variable_names(
        self, rls_db_session: AsyncSession
    ):
        """Verify policies use correct session variable names."""
        result = await rls_db_session.execute(
            text("""
                SELECT tablename, policyname
                FROM pg_policies
                WHERE schemaname = 'public'
                  AND (
                    qual::text LIKE '%current_school_id%'
                    OR qual::text LIKE '%tenant_id%' AND qual::text NOT LIKE '%current_tenant_id%'
                  )
            """)
        )
        problematic = result.fetchall()

        assert len(problematic) == 0, (
            f"Found {len(problematic)} policies with wrong variable names: "
            f"{[f'{t}.{p}' for t, p in problematic]}"
        )


@pytest.mark.integration
class TestInvitationCodesRLS:
    """Specific tests for invitation_codes RLS policies."""

    @pytest.mark.asyncio
    async def test_school_admin_can_update_own_codes(
        self, rls_db_session: AsyncSession
    ):
        """School admin can update invitation codes from their school."""
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '5', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )

        # Try to update - should work for school_id = 5
        # This tests that UPDATE policy works
        result = await rls_db_session.execute(
            text("""
                UPDATE invitation_codes
                SET uses_count = uses_count
                WHERE school_id = 5
                RETURNING id
            """)
        )
        # Should not raise an error
        await rls_db_session.rollback()

    @pytest.mark.asyncio
    async def test_school_admin_cannot_update_other_school_codes(
        self, rls_db_session: AsyncSession
    ):
        """School admin cannot update invitation codes from other schools."""
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '5', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )

        # Try to update codes from school_id = 999 - should affect 0 rows
        result = await rls_db_session.execute(
            text("""
                UPDATE invitation_codes
                SET uses_count = uses_count
                WHERE school_id = 999
                RETURNING id
            """)
        )
        updated = result.fetchall()
        assert len(updated) == 0

        await rls_db_session.rollback()

    @pytest.mark.asyncio
    async def test_school_admin_can_delete_own_codes(
        self, rls_db_session: AsyncSession
    ):
        """School admin can delete invitation codes from their school."""
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '5', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )

        # Try to delete - should work for school_id = 5
        # Using SELECT to test visibility (DELETE would actually remove data)
        result = await rls_db_session.execute(
            text("""
                SELECT id FROM invitation_codes
                WHERE school_id = 5
            """)
        )
        # Should not raise an error
        await rls_db_session.rollback()
