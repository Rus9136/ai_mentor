"""fix_test_attempts_rls_policies

Fix RLS policies for test_attempts and test_attempt_answers tables:
1. Fix test_attempts policies to use NULLIF+COALESCE pattern
2. Add missing policy for test_attempt_answers
3. Sync test_attempts_id_seq1 sequence

Revision ID: b7d8e9f0a1b2
Revises: a6f786ce22f9
Create Date: 2026-01-14 15:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b7d8e9f0a1b2'
down_revision: Union[str, None] = 'a6f786ce22f9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix RLS policies for test_attempts and test_attempt_answers.

    Problem: Previous policies used incorrect COALESCE pattern that failed
    when session variables were empty strings (not NULL).

    Solution: Use COALESCE(NULLIF(current_setting(...), ''), 'default')
    to handle both NULL and empty string cases.
    """

    # ===========================================
    # 1. Fix test_attempts RLS policies
    # ===========================================
    # Drop existing policies
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempts;")
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON test_attempts;")

    # Create fixed SELECT/UPDATE/DELETE policy
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON test_attempts
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # Create fixed INSERT policy
    op.execute("""
        CREATE POLICY tenant_insert_policy ON test_attempts
        FOR INSERT
        TO PUBLIC
        WITH CHECK (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # ===========================================
    # 2. Fix test_attempt_answers RLS policy
    # ===========================================
    # Ensure RLS is enabled
    op.execute("ALTER TABLE test_attempt_answers ENABLE ROW LEVEL SECURITY;")

    # Drop existing policy if any
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempt_answers;")

    # Create policy that inherits from test_attempts
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON test_attempt_answers
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM test_attempts
                WHERE test_attempts.id = test_attempt_answers.attempt_id
                AND test_attempts.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)

    # ===========================================
    # 3. Sync test_attempts_id_seq1 sequence
    # ===========================================
    # This ensures the sequence is ahead of all existing IDs
    op.execute("""
        SELECT setval(
            'test_attempts_id_seq1',
            COALESCE((SELECT MAX(id) FROM test_attempts), 0) + 1,
            false
        );
    """)


def downgrade() -> None:
    """
    Revert to previous RLS policies.
    Note: This restores potentially broken policies - use with caution.
    """
    # Restore test_attempts policies (original from partition migration)
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempts;")
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON test_attempts;")

    op.execute("""
        CREATE POLICY tenant_isolation_policy ON test_attempts
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );
    """)

    op.execute("""
        CREATE POLICY tenant_insert_policy ON test_attempts
        FOR INSERT
        WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );
    """)

    # Restore test_attempt_answers policy
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempt_answers;")

    op.execute("""
        CREATE POLICY tenant_isolation_policy ON test_attempt_answers
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM test_attempts
                WHERE test_attempts.id = test_attempt_answers.attempt_id
                AND test_attempts.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)
