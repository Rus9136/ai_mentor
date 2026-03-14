"""Deactivate study_time and review_spaced daily quests (no tracking mechanism).

Revision ID: 053_deactivate_orphan_quests
Revises: 052_quiz_sessions
"""

from alembic import op

revision = '053_deactivate_orphan_quests'
down_revision = '052_quiz_sessions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # study_30_min (quest_type=study_time) and review_2_spaced (quest_type=review_spaced)
    # have no backend hooks to track progress, making them impossible to complete.
    # Deactivate until tracking is implemented.
    op.execute("""
        UPDATE daily_quests
        SET is_active = false
        WHERE code IN ('study_30_min', 'review_2_spaced');
    """)

    op.execute("""
        UPDATE alembic_version
        SET version_num = '053_deactivate_orphan_quests'
        WHERE version_num = '052_quiz_sessions';
    """)


def downgrade() -> None:
    op.execute("""
        UPDATE daily_quests
        SET is_active = true
        WHERE code IN ('study_30_min', 'review_2_spaced');
    """)

    op.execute("""
        UPDATE alembic_version
        SET version_num = '052_quiz_sessions'
        WHERE version_num = '053_deactivate_orphan_quests';
    """)
