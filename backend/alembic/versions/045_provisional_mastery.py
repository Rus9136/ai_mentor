"""Add is_provisional column to chapter_mastery.

Revision ID: 045_provisional_mastery
Revises: 044_review_schedule
"""

from alembic import op

revision = '045_provisional_mastery'
down_revision = '044_review_schedule'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE chapter_mastery
        ADD COLUMN is_provisional BOOLEAN NOT NULL DEFAULT FALSE;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE chapter_mastery DROP COLUMN IF EXISTS is_provisional;")
