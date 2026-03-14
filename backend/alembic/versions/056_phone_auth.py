"""Add phone authentication support.

Revision ID: 056_phone_auth
Revises: 055_fix_rls_school_id_variable
Create Date: 2026-03-14
"""

from alembic import op


revision = '056_phone_auth'
down_revision = '055_fix_rls_school_id_variable'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'phone' value to authprovider enum
    op.execute("ALTER TYPE authprovider ADD VALUE IF NOT EXISTS 'phone'")

    # Clean up empty phone strings before creating unique index
    op.execute("UPDATE users SET phone = NULL WHERE phone = ''")

    # Create unique partial index on phone (only for non-null, non-deleted users)
    op.execute(
        "CREATE UNIQUE INDEX ix_users_phone_unique "
        "ON users (phone) "
        "WHERE phone IS NOT NULL AND is_deleted = false"
    )


def downgrade() -> None:
    # Drop partial unique index
    op.execute("DROP INDEX IF EXISTS ix_users_phone_unique")

    # Note: Cannot remove enum value in PostgreSQL - this is a known limitation
    # The 'phone' value will remain in the enum type
