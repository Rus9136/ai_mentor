"""Add metacognitive_pattern columns to students.

Revision ID: 046_metacognitive_pattern
Revises: 045_provisional_mastery
"""

from alembic import op

revision = '046_metacognitive_pattern'
down_revision = '045_provisional_mastery'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE students
        ADD COLUMN metacognitive_pattern VARCHAR(20) DEFAULT NULL,
        ADD COLUMN metacognitive_updated_at TIMESTAMPTZ DEFAULT NULL;
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS metacognitive_pattern;")
    op.execute("ALTER TABLE students DROP COLUMN IF EXISTS metacognitive_updated_at;")
