"""RLS Policy Audit Tests.

Automatically detect inconsistencies in RLS policies BEFORE they hit production.
These tests query pg_policies and verify structural consistency.

Run: pytest backend/tests/test_rls_policy_audit.py -v

This would have caught the DELETE /auth/me bug where students_modify_policy
(UPDATE) was missing user_id check that SELECT/INSERT policies had.
"""

import pytest
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import NullPool

from app.core.config import settings


PROD_DATABASE_URL = (
    f"postgresql+asyncpg://ai_mentor_app:{settings.POSTGRES_PASSWORD}"
    f"@{settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}/{settings.POSTGRES_DB}"
)


@pytest.fixture
async def rls_db_session():
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
        pytest.skip(f"Cannot connect to DB for RLS audit: {e}")


@pytest.mark.integration
class TestRLSPolicyAudit:
    """Structural audit of all RLS policies."""

    @pytest.mark.asyncio
    async def test_all_rls_tables_have_all_four_operations(
        self, rls_db_session: AsyncSession
    ):
        """Every table with RLS should have SELECT, INSERT, UPDATE, DELETE policies."""
        result = await rls_db_session.execute(
            text("""
                SELECT tablename,
                       array_agg(DISTINCT cmd ORDER BY cmd) as commands
                FROM pg_policies
                WHERE schemaname = 'public'
                GROUP BY tablename
            """)
        )
        rows = result.fetchall()
        missing = []
        expected_cmds = {'r', 'a', 'w', 'd'}  # SELECT, INSERT, UPDATE, DELETE
        cmd_names = {'r': 'SELECT', 'a': 'INSERT', 'w': 'UPDATE', 'd': 'DELETE'}

        for tablename, commands in rows:
            cmds_set = set(commands)
            diff = expected_cmds - cmds_set
            if diff:
                names = [cmd_names[c] for c in diff]
                missing.append(f"{tablename}: missing {', '.join(names)}")

        assert not missing, (
            f"Tables with incomplete RLS policies:\n" +
            "\n".join(f"  - {m}" for m in missing)
        )

    @pytest.mark.asyncio
    async def test_user_id_consistency_across_operations(
        self, rls_db_session: AsyncSession
    ):
        """If SELECT policy uses current_user_id, UPDATE should too.

        This is the exact bug that caused DELETE /auth/me to fail:
        SELECT had user_id check, UPDATE didn't.
        """
        result = await rls_db_session.execute(
            text("""
                SELECT tablename, policyname, cmd,
                       COALESCE(qual, '') || ' ' || COALESCE(with_check, '') as full_policy
                FROM pg_policies
                WHERE schemaname = 'public'
            """)
        )
        rows = result.fetchall()

        # Group by table
        table_policies = {}
        for tablename, policyname, cmd, full_policy in rows:
            if tablename not in table_policies:
                table_policies[tablename] = {}
            table_policies[tablename][cmd] = {
                'name': policyname,
                'has_user_id': 'current_user_id' in full_policy,
                'has_tenant_id': 'current_tenant_id' in full_policy,
                'has_super_admin': 'is_super_admin' in full_policy,
            }

        inconsistencies = []
        for table, policies in table_policies.items():
            select_policy = policies.get('r', {})
            update_policy = policies.get('w', {})
            delete_policy = policies.get('d', {})

            # If SELECT allows user_id, UPDATE and DELETE should too
            if select_policy.get('has_user_id') and update_policy and not update_policy.get('has_user_id'):
                inconsistencies.append(
                    f"{table}: SELECT has user_id check but UPDATE "
                    f"({update_policy['name']}) does NOT"
                )
            if select_policy.get('has_user_id') and delete_policy and not delete_policy.get('has_user_id'):
                inconsistencies.append(
                    f"{table}: SELECT has user_id check but DELETE "
                    f"({delete_policy['name']}) does NOT"
                )

        assert not inconsistencies, (
            f"RLS user_id inconsistencies (SELECT allows but write doesn't):\n" +
            "\n".join(f"  - {i}" for i in inconsistencies)
        )

    @pytest.mark.asyncio
    async def test_tenant_id_consistency_across_operations(
        self, rls_db_session: AsyncSession
    ):
        """If any policy uses tenant_id, all CRUD policies should."""
        result = await rls_db_session.execute(
            text("""
                SELECT tablename, cmd,
                       COALESCE(qual, '') || ' ' || COALESCE(with_check, '') as full_policy
                FROM pg_policies
                WHERE schemaname = 'public'
            """)
        )
        rows = result.fetchall()

        table_policies = {}
        for tablename, cmd, full_policy in rows:
            if tablename not in table_policies:
                table_policies[tablename] = {}
            table_policies[tablename][cmd] = 'current_tenant_id' in full_policy

        cmd_names = {'r': 'SELECT', 'a': 'INSERT', 'w': 'UPDATE', 'd': 'DELETE'}
        inconsistencies = []
        for table, cmds in table_policies.items():
            has_tenant = [c for c, v in cmds.items() if v]
            no_tenant = [c for c, v in cmds.items() if not v]
            if has_tenant and no_tenant:
                has_names = [cmd_names.get(c, c) for c in has_tenant]
                no_names = [cmd_names.get(c, c) for c in no_tenant]
                inconsistencies.append(
                    f"{table}: tenant_id in {has_names} but NOT in {no_names}"
                )

        assert not inconsistencies, (
            f"RLS tenant_id inconsistencies:\n" +
            "\n".join(f"  - {i}" for i in inconsistencies)
        )

    @pytest.mark.asyncio
    async def test_student_can_update_own_record(
        self, rls_db_session: AsyncSession
    ):
        """Verify a student (with user_id but no matching tenant) can update own record.

        Regression test for the DELETE /auth/me StaleDataError bug.
        """
        # Get any student to test with
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'true', true)")
        )
        result = await rls_db_session.execute(
            text("SELECT id, user_id, school_id FROM students LIMIT 1")
        )
        student = result.fetchone()
        if not student:
            pytest.skip("No students in database")

        student_id, user_id, school_id = student

        # Now simulate student context: user_id set, but tenant_id is different
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.current_user_id', :uid, true)"),
            {"uid": str(user_id)}
        )
        # Set tenant to 0 (no school match) to specifically test user_id path
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '0', true)")
        )

        # SELECT should work via user_id
        result = await rls_db_session.execute(
            text("SELECT id FROM students WHERE id = :sid"),
            {"sid": student_id}
        )
        assert result.fetchone() is not None, "SELECT by user_id should work"

        # UPDATE should also work via user_id (this was the bug)
        result = await rls_db_session.execute(
            text("""
                UPDATE students SET updated_at = updated_at
                WHERE id = :sid
                RETURNING id
            """),
            {"sid": student_id}
        )
        updated = result.fetchone()
        assert updated is not None, (
            "UPDATE by user_id should work — "
            "students_modify_policy must include user_id check"
        )

        await rls_db_session.rollback()

    @pytest.mark.asyncio
    async def test_cross_tenant_update_blocked(
        self, rls_db_session: AsyncSession
    ):
        """Verify a user cannot update records from another school."""
        await rls_db_session.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.current_user_id', '0', true)")
        )
        await rls_db_session.execute(
            text("SELECT set_config('app.current_tenant_id', '999999', true)")
        )

        result = await rls_db_session.execute(
            text("""
                UPDATE students SET updated_at = updated_at
                RETURNING id
            """)
        )
        assert result.fetchone() is None, "Cross-tenant update must be blocked"

        await rls_db_session.rollback()
