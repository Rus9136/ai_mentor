"""Add Apple OAuth support

Revision ID: 029_add_apple_oauth
Revises: 028_add_homework_attachments
Create Date: 2026-02-04

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '029_add_apple_oauth'
down_revision = '028_add_homework_attachments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add 'apple' value to authprovider enum
    op.execute("ALTER TYPE authprovider ADD VALUE IF NOT EXISTS 'apple'")

    # Add apple_id column to users table
    op.add_column('users', sa.Column('apple_id', sa.String(255), nullable=True))

    # Create unique index on apple_id
    op.create_index('ix_users_apple_id', 'users', ['apple_id'], unique=True)


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_users_apple_id', table_name='users')

    # Drop column
    op.drop_column('users', 'apple_id')

    # Note: Cannot remove enum value in PostgreSQL - this is a known limitation
    # The 'apple' value will remain in the enum type
