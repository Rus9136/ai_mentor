"""Fix RLS type consistency - remove ::boolean casts

This migration fixes RLS policies that use unsafe ::boolean casts.
The problem: COALESCE(current_setting(...), 'false')::boolean can fail
if the value is an empty string (which cannot be cast to boolean).

Fixed policies:
- invitation_codes_update_policy
- invitation_codes_delete_policy
- invitation_code_uses_select_policy

Changed from:
  COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true

To (safe pattern):
  COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'

Revision ID: 024
Revises: 023
Create Date: 2026-01-07
"""

from typing import Sequence, Union

from alembic import op


revision: str = "024"
down_revision: Union[str, None] = "023"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Safe patterns for RLS policies
SUPER_ADMIN_CHECK = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"
TENANT_ID_MATCH = "school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer"


def upgrade() -> None:
    """Fix RLS policies with unsafe ::boolean casts."""

    # === invitation_codes ===
    # Drop old policies with ::boolean cast
    op.execute("DROP POLICY IF EXISTS invitation_codes_update_policy ON invitation_codes;")
    op.execute("DROP POLICY IF EXISTS invitation_codes_delete_policy ON invitation_codes;")

    # Recreate with safe string comparison
    op.execute(f"""
        CREATE POLICY invitation_codes_update_policy ON invitation_codes
        FOR UPDATE
        USING (
            ({SUPER_ADMIN_CHECK})
            OR ({TENANT_ID_MATCH})
        );
    """)

    op.execute(f"""
        CREATE POLICY invitation_codes_delete_policy ON invitation_codes
        FOR DELETE
        USING (
            ({SUPER_ADMIN_CHECK})
            OR ({TENANT_ID_MATCH})
        );
    """)

    # === invitation_code_uses ===
    # Drop old policy with ::boolean cast
    op.execute("DROP POLICY IF EXISTS invitation_code_uses_select_policy ON invitation_code_uses;")

    # Recreate with safe string comparison
    op.execute(f"""
        CREATE POLICY invitation_code_uses_select_policy ON invitation_code_uses
        FOR SELECT
        USING (
            ({SUPER_ADMIN_CHECK})
            OR invitation_code_id IN (
                SELECT id FROM invitation_codes
                WHERE {TENANT_ID_MATCH}
            )
        );
    """)


def downgrade() -> None:
    """Restore original policies with ::boolean casts (not recommended)."""

    # === invitation_codes ===
    op.execute("DROP POLICY IF EXISTS invitation_codes_update_policy ON invitation_codes;")
    op.execute("DROP POLICY IF EXISTS invitation_codes_delete_policy ON invitation_codes;")

    op.execute("""
        CREATE POLICY invitation_codes_update_policy ON invitation_codes
        FOR UPDATE
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        );
    """)

    op.execute("""
        CREATE POLICY invitation_codes_delete_policy ON invitation_codes
        FOR DELETE
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        );
    """)

    # === invitation_code_uses ===
    op.execute("DROP POLICY IF EXISTS invitation_code_uses_select_policy ON invitation_code_uses;")

    op.execute("""
        CREATE POLICY invitation_code_uses_select_policy ON invitation_code_uses
        FOR SELECT
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR invitation_code_id IN (
                SELECT id FROM invitation_codes
                WHERE school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
            )
        );
    """)
