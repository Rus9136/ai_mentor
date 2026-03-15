"""Add created_at/updated_at to quiz_participants and quiz_answers.

These columns are expected by BaseModel (TimestampMixin) but were missing
from the original migration.

Revision ID: 057_quiz_timestamp_columns
Revises: 056_phone_auth
"""

from alembic import op

revision = '057_quiz_timestamp_columns'
down_revision = '056_phone_auth'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE quiz_participants
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
    """)

    op.execute("""
        ALTER TABLE quiz_answers
        ADD COLUMN IF NOT EXISTS created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
        ADD COLUMN IF NOT EXISTS updated_at TIMESTAMPTZ NOT NULL DEFAULT now();
    """)

    op.execute("""
        UPDATE alembic_version
        SET version_num = '057_quiz_timestamp_columns'
        WHERE version_num = '056_phone_auth';
    """)


def downgrade() -> None:
    op.execute("""
        ALTER TABLE quiz_participants
        DROP COLUMN IF EXISTS created_at,
        DROP COLUMN IF EXISTS updated_at;
    """)

    op.execute("""
        ALTER TABLE quiz_answers
        DROP COLUMN IF EXISTS created_at,
        DROP COLUMN IF EXISTS updated_at;
    """)

    op.execute("""
        UPDATE alembic_version
        SET version_num = '056_phone_auth'
        WHERE version_num = '057_quiz_timestamp_columns';
    """)
