"""Add current_streak and max_streak columns to quiz_participants.

Revision ID: 054_quiz_streak_columns
Revises: 053_deactivate_orphan_quests
"""

from alembic import op

revision = '054_quiz_streak_columns'
down_revision = '053_deactivate_orphan_quests'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE quiz_participants
        ADD COLUMN current_streak INTEGER NOT NULL DEFAULT 0,
        ADD COLUMN max_streak INTEGER NOT NULL DEFAULT 0;
    """)

    op.execute("""
        UPDATE alembic_version
        SET version_num = '054_quiz_streak_columns'
        WHERE version_num = '053_deactivate_orphan_quests';
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE quiz_participants
        DROP COLUMN IF EXISTS current_streak,
        DROP COLUMN IF EXISTS max_streak;
    """)

    op.execute("""
        UPDATE alembic_version
        SET version_num = '053_deactivate_orphan_quests'
        WHERE version_num = '054_quiz_streak_columns';
    """)
