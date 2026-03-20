"""RLS Super Admin Bypass Audit.

Ensures every RLS policy that filters by current_tenant_id
also includes the is_super_admin bypass. Without this bypass, SUPER_ADMIN
sees zero rows because tenant_id=NULL falls through to school_id=0.

This is the exact bug that broke /admin/global/llm-usage in March 2026:
migration 055 added tenant_id filtering but forgot the super_admin bypass
on 8 tables.

Two test classes:
  1. TestRLSMigrationLint — static analysis of migration files (runs in CI, no DB needed)
  2. TestRLSSuperAdminBypass — runtime check against live DB (runs locally)

Run: pytest backend/tests/test_rls_super_admin_bypass.py -v
"""

import re
from pathlib import Path

import pytest

# ---------------------------------------------------------------------------
# 1. Static analysis — scans migration files, runs in CI without DB
# ---------------------------------------------------------------------------

MIGRATIONS_DIR = Path(__file__).parent.parent / "alembic" / "versions"


def _extract_upgrade_body(content: str) -> str:
    """Extract only the upgrade() function body from a migration file."""
    match = re.search(
        r"def upgrade\(\).*?:\n(.*?)(?=\ndef |\Z)",
        content,
        re.DOTALL,
    )
    return match.group(1) if match else ""


def _extract_create_policies(sql_block: str) -> list[tuple[str, str, str]]:
    """Extract (policy_name, table_name, full_statement) from SQL text.

    Handles multi-line CREATE POLICY statements.
    """
    results = []
    pattern = re.compile(
        r"CREATE\s+POLICY\s+(\w+)\s+ON\s+(\w+)\s+"
        r"(.*?)(?=CREATE\s+POLICY|DROP\s+POLICY|ALTER\s|GRANT\s|CREATE\s+(?:TABLE|INDEX|TYPE)|$)",
        re.IGNORECASE | re.DOTALL,
    )
    for match in pattern.finditer(sql_block):
        policy_name = match.group(1)
        table_name = match.group(2)
        full_stmt = match.group(0)
        results.append((policy_name, table_name, full_stmt))
    return results


def _extract_drop_policies(sql_block: str) -> list[tuple[str, str]]:
    """Extract (policy_name, table_name) from DROP POLICY statements."""
    results = []
    pattern = re.compile(
        r"DROP\s+POLICY\s+(?:IF\s+EXISTS\s+)?(\w+)\s+ON\s+(\w+)",
        re.IGNORECASE,
    )
    for match in pattern.finditer(sql_block):
        results.append((match.group(1), match.group(2)))
    return results


class TestRLSMigrationLint:
    """Static analysis of migration files for RLS policy correctness.

    No database connection needed — parses Python source files.
    Safe to run in CI.
    """

    def test_tenant_policies_have_super_admin_bypass(self):
        """Every CREATE POLICY with current_tenant_id must also check is_super_admin.

        Only checks upgrade() functions. Tracks DROP POLICY to avoid
        flagging policies that were replaced by later migrations.
        """
        if not MIGRATIONS_DIR.exists():
            pytest.skip(f"Migrations dir not found: {MIGRATIONS_DIR}")

        # Track: (table, policy_name) -> (filename, sql)
        active_policies: dict[tuple[str, str], tuple[str, str]] = {}
        # Track dropped policies
        dropped: set[tuple[str, str]] = set()

        for filepath in sorted(MIGRATIONS_DIR.glob("*.py")):
            if filepath.name == "__init__.py":
                continue

            content = filepath.read_text()
            upgrade_body = _extract_upgrade_body(content)
            if not upgrade_body:
                continue

            # Track drops first
            for policy_name, table_name in _extract_drop_policies(upgrade_body):
                dropped.add((table_name, policy_name))
                active_policies.pop((table_name, policy_name), None)

            # Then track creates (a later CREATE overrides a DROP in same file)
            for policy_name, table_name, full_stmt in _extract_create_policies(upgrade_body):
                active_policies[(table_name, policy_name)] = (
                    filepath.name,
                    full_stmt,
                )

        # Check each active policy
        missing_bypass = []
        for (table_name, policy_name), (filename, sql) in active_policies.items():
            # Only check policies that use current_tenant_id
            if "current_tenant_id" not in sql:
                continue

            if "is_super_admin" not in sql:
                missing_bypass.append(
                    f"  {table_name}.{policy_name} (in {filename})"
                )

        assert not missing_bypass, (
            "RLS policies with current_tenant_id filtering "
            "but WITHOUT is_super_admin bypass:\n"
            + "\n".join(missing_bypass)
            + "\n\nFix: add "
            "(COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true') OR ... "
            "to the USING clause."
        )

    def test_no_old_school_id_variable_in_new_migrations(self):
        """Migrations after 055 should not use app.current_school_id in upgrade()."""
        if not MIGRATIONS_DIR.exists():
            pytest.skip(f"Migrations dir not found: {MIGRATIONS_DIR}")

        violations = []
        found_055 = False

        for filepath in sorted(MIGRATIONS_DIR.glob("*.py")):
            if filepath.name == "__init__.py":
                continue
            if "055" in filepath.name:
                found_055 = True
                continue
            if not found_055:
                continue

            content = filepath.read_text()
            upgrade_body = _extract_upgrade_body(content)

            if "current_school_id" in upgrade_body:
                violations.append(filepath.name)

        assert not violations, (
            "Migrations after 055 use old 'app.current_school_id' in upgrade():\n"
            + "\n".join(f"  - {v}" for v in violations)
            + "\n\nUse 'app.current_tenant_id' instead."
        )


# ---------------------------------------------------------------------------
# 2. Runtime check — queries pg_policies on live DB (local only)
# ---------------------------------------------------------------------------

try:
    import os

    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import (
        create_async_engine,
        AsyncSession,
        async_sessionmaker,
    )
    from sqlalchemy.pool import NullPool
    from app.core.config import settings

    # Use TEST_DB_HOST/PORT overrides for local runs (Docker exposes on localhost:5435)
    _host = os.environ.get("TEST_DB_HOST", settings.POSTGRES_HOST)
    _port = os.environ.get("TEST_DB_PORT", str(settings.POSTGRES_PORT))

    # Connect as ai_mentor_user (superuser) then SET ROLE to ai_mentor_app for RLS tests
    PROD_DATABASE_URL = (
        f"postgresql+asyncpg://ai_mentor_user:{settings.POSTGRES_PASSWORD}"
        f"@{_host}:{_port}/{settings.POSTGRES_DB}"
    )
    HAS_DB = True
except Exception:
    HAS_DB = False


@pytest.fixture
async def rls_db():
    if not HAS_DB:
        pytest.skip("DB not available")
    engine = None
    try:
        engine = create_async_engine(PROD_DATABASE_URL, poolclass=NullPool)
        session_maker = async_sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with session_maker() as session:
            # Verify connection works
            await session.execute(text("SELECT 1"))
            yield session
            await session.rollback()
    except Exception as e:
        pytest.skip(f"Cannot connect to DB: {e}")
    finally:
        if engine:
            await engine.dispose()


@pytest.mark.integration
class TestRLSSuperAdminBypass:
    """Runtime audit: verify all tenant-filtered policies have super_admin bypass."""

    @pytest.mark.asyncio
    async def test_all_tenant_policies_have_super_admin_bypass(self, rls_db):
        """Query pg_policies: every policy with current_tenant_id must have is_super_admin."""
        result = await rls_db.execute(
            text("""
                SELECT tablename, policyname,
                       COALESCE(qual::text, '') || ' ' || COALESCE(with_check::text, '') as full_sql
                FROM pg_policies
                WHERE schemaname = 'public'
            """)
        )
        rows = result.fetchall()

        missing = []
        for tablename, policyname, full_sql in rows:
            if "current_tenant_id" not in full_sql:
                continue
            if "is_super_admin" not in full_sql:
                missing.append(f"{tablename}.{policyname}")

        assert not missing, (
            "RLS policies with current_tenant_id but WITHOUT is_super_admin bypass:\n"
            + "\n".join(f"  - {m}" for m in missing)
        )

    @pytest.mark.asyncio
    async def test_super_admin_sees_all_llm_usage_logs(self, rls_db):
        """Regression: SUPER_ADMIN must see all llm_usage_logs regardless of school_id."""
        # Switch to ai_mentor_app role (RLS enforced)
        await rls_db.execute(text("SET ROLE ai_mentor_app"))

        # Count as SUPER_ADMIN
        await rls_db.execute(
            text("SELECT set_config('app.is_super_admin', 'true', true)")
        )
        await rls_db.execute(
            text("SELECT set_config('app.current_tenant_id', '', true)")
        )
        await rls_db.execute(
            text("SELECT set_config('app.current_user_id', '1', true)")
        )

        result = await rls_db.execute(
            text("SELECT count(*) FROM llm_usage_logs")
        )
        sa_count = result.scalar()

        # Count as regular user with tenant=0 (should see fewer or zero)
        await rls_db.execute(
            text("SELECT set_config('app.is_super_admin', 'false', true)")
        )
        await rls_db.execute(
            text("SELECT set_config('app.current_tenant_id', '0', true)")
        )
        result = await rls_db.execute(
            text("SELECT count(*) FROM llm_usage_logs")
        )
        tenant0_count = result.scalar()

        # Reset role
        await rls_db.execute(text("RESET ROLE"))

        assert sa_count >= tenant0_count, (
            f"SUPER_ADMIN sees {sa_count} rows but tenant=0 sees {tenant0_count}. "
            "is_super_admin bypass is broken!"
        )
