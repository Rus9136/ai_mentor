"""Fix users RLS policy to allow OAuth registration with NULL school_id

Revision ID: 016
Revises: 015
Create Date: 2025-12-18

"""
from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = '016'
down_revision: Union[str, None] = '015'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Drop existing INSERT policy
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON users")
    
    # Create new policy that allows:
    # 1. SUPER_ADMIN can insert any user
    # 2. Users with matching school_id can be inserted
    # 3. Users with NULL school_id can be inserted (OAuth registration, SUPER_ADMIN users)
    op.execute("""
        CREATE POLICY tenant_insert_policy ON users
        FOR INSERT
        WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id IS NULL
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        )
    """)


def downgrade() -> None:
    # Restore original policy
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON users")
    op.execute("""
        CREATE POLICY tenant_insert_policy ON users
        FOR INSERT
        WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        )
    """)
