"""Add SUPER_ADMIN role to UserRole enum

Revision ID: 009
Revises: 008
Create Date: 2025-10-29

This migration adds the SUPER_ADMIN role to the UserRole enum and makes
school_id nullable for users to support SUPER_ADMIN users who are not
tied to a specific school.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '009'
down_revision: Union[str, None] = '008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'super_admin' value to the userrole enum
    # Note: ALTER TYPE ... ADD VALUE cannot be executed in a transaction block
    # Alembic will handle this automatically
    op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'super_admin'")

    # Make school_id nullable for SUPER_ADMIN users
    op.alter_column(
        'users',
        'school_id',
        existing_type=sa.Integer(),
        nullable=True
    )


def downgrade() -> None:
    # Make school_id NOT NULL again
    # WARNING: This will fail if there are any SUPER_ADMIN users with NULL school_id
    op.alter_column(
        'users',
        'school_id',
        existing_type=sa.Integer(),
        nullable=False
    )

    # Note: PostgreSQL does not support removing enum values
    # The 'super_admin' value will remain in the enum type
    # If you need to remove it, you would need to:
    # 1. Create a new enum without 'super_admin'
    # 2. Alter the column to use the new enum
    # 3. Drop the old enum
    # This is not implemented here for safety reasons
    pass
