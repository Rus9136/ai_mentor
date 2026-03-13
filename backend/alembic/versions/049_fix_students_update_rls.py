"""Fix students UPDATE RLS policy to allow user_id match.

The students_modify_policy (UPDATE) was missing the user_id check,
causing DELETE /auth/me to fail with StaleDataError when a student
tries to soft-delete their own account.

SELECT and INSERT policies already allowed user_id matching.

Revision ID: 049_fix_students_update_rls
Revises: 048_usage_limits
"""

from alembic import op

revision = '049_fix_students_update_rls'
down_revision = '048_usage_limits'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("DROP POLICY IF EXISTS students_modify_policy ON students")
    op.execute("""
        CREATE POLICY students_modify_policy ON students FOR UPDATE
        USING (
            (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
            OR (user_id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0')::integer)
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS students_modify_policy ON students")
    op.execute("""
        CREATE POLICY students_modify_policy ON students FOR UPDATE
        USING (
            (COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
        )
    """)
