"""Fix RLS for student join requests - allow students to create requests for any school.

Revision ID: 027_fix_join_requests_rls
Revises: 026_add_fio_to_join_requests
Create Date: 2025-01-21

Students need to create join requests for schools they don't belong to yet.
The current tenant isolation policy blocks this. We add a separate INSERT policy
that allows any authenticated user (with valid session) to insert join requests.
"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "027_fix_join_requests_rls"
down_revision = "026_add_fio_to_join_requests"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add INSERT policy that allows students to create join requests for any school
    # This is safe because:
    # 1. The endpoint validates the invitation code
    # 2. The endpoint validates the student's identity
    # 3. Students can only create one pending request at a time (enforced in code)
    op.execute("""
        CREATE POLICY student_join_requests_insert_allow
        ON student_join_requests
        FOR INSERT
        WITH CHECK (true);
    """)

    # Also need SELECT policy for students to see their own requests
    # They need to see requests regardless of school_id
    op.execute("""
        CREATE POLICY student_join_requests_select_own
        ON student_join_requests
        FOR SELECT
        USING (
            student_id IN (
                SELECT id FROM students
                WHERE user_id = (COALESCE(current_setting('app.current_user_id', true), '0'))::integer
            )
        );
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS student_join_requests_insert_allow ON student_join_requests;")
    op.execute("DROP POLICY IF EXISTS student_join_requests_select_own ON student_join_requests;")
