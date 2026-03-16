"""Fix student_join_requests RLS policies — add NULLIF for empty string handling.

The tenant_isolation and select_own policies used COALESCE without NULLIF,
so when app.current_tenant_id or app.current_user_id was reset to empty string
(e.g. during onboarding with school_id=NULL), COALESCE('', '0') returns ''
instead of '0', and ''::integer crashes with InvalidTextRepresentationError.

This matches the pattern already used in the students table policies.

Revision ID: 062_fix_join_requests_rls
Revises: 061_weekly_tournaments
"""

from alembic import op


revision = "062_fix_join_requests_rls"
down_revision = "061_weekly_tournaments"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old broken policies
    op.execute("DROP POLICY IF EXISTS student_join_requests_tenant_isolation ON student_join_requests")
    op.execute("DROP POLICY IF EXISTS student_join_requests_select_own ON student_join_requests")

    # Recreate tenant_isolation with NULLIF to handle empty string from set_config(NULL)
    op.execute("""
        CREATE POLICY student_join_requests_tenant_isolation ON student_join_requests
        FOR ALL
        USING (
            (COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0'))::integer = 0
            OR school_id = (COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0'))::integer
        )
    """)

    # Recreate select_own with NULLIF
    op.execute("""
        CREATE POLICY student_join_requests_select_own ON student_join_requests
        FOR SELECT
        USING (
            student_id IN (
                SELECT s.id FROM students s
                WHERE s.user_id = (COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0'))::integer
            )
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS student_join_requests_tenant_isolation ON student_join_requests")
    op.execute("DROP POLICY IF EXISTS student_join_requests_select_own ON student_join_requests")

    op.execute("""
        CREATE POLICY student_join_requests_tenant_isolation ON student_join_requests
        FOR ALL
        USING (
            (COALESCE(current_setting('app.current_tenant_id', true), '0'))::integer = 0
            OR school_id = (COALESCE(current_setting('app.current_tenant_id', true), '0'))::integer
        )
    """)

    op.execute("""
        CREATE POLICY student_join_requests_select_own ON student_join_requests
        FOR SELECT
        USING (
            student_id IN (
                SELECT s.id FROM students s
                WHERE s.user_id = (COALESCE(current_setting('app.current_user_id', true), '0'))::integer
            )
        )
    """)
