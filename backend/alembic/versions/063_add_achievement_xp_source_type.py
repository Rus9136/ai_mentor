"""Add 'achievement' value to xp_source_type enum.

Previously achievement XP was incorrectly recorded as 'mastery_up',
making it impossible to distinguish achievement rewards from mastery
change rewards in analytics and creating potential source_id collisions.

Revision ID: 063_achievement_xp_source
Revises: 062_fix_join_requests_rls
"""

from alembic import op


revision = "063_achievement_xp_source"
down_revision = "062_fix_join_requests_rls"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE xp_source_type ADD VALUE IF NOT EXISTS 'achievement'")

    # Fix existing achievement XP transactions that were recorded as 'mastery_up'.
    # Achievement transactions have extra_data->>'achievement_code' set.
    op.execute("""
        UPDATE xp_transactions
        SET source_type = 'achievement'
        WHERE source_type = 'mastery_up'
          AND metadata->>'achievement_code' IS NOT NULL
    """)


def downgrade() -> None:
    # Revert transactions back to mastery_up
    op.execute("""
        UPDATE xp_transactions
        SET source_type = 'mastery_up'
        WHERE source_type = 'achievement'
    """)
    # Note: PostgreSQL does not support removing enum values
