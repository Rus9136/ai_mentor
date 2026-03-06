"""Add updated_at column to paragraph_outcomes table.

The paragraph_outcomes model inherits TimestampMixin (created_at + updated_at),
but the original migration only created created_at. This was discovered when
the lesson plan generator tried to query paragraph outcomes with selectinload.

Fixed manually on production 2026-03-06, this migration formalizes the change.

Revision ID: 037_outcomes_updated_at
Revises: 036_audio_text
"""
from alembic import op
import sqlalchemy as sa

revision = "037_outcomes_updated_at"
down_revision = "036_audio_text"
branch_labels = None
depends_on = None


def upgrade():
    # Column may already exist (was added manually on production)
    conn = op.get_bind()
    result = conn.execute(
        sa.text(
            "SELECT 1 FROM information_schema.columns "
            "WHERE table_name = 'paragraph_outcomes' AND column_name = 'updated_at'"
        )
    )
    if not result.fetchone():
        op.add_column(
            "paragraph_outcomes",
            sa.Column(
                "updated_at",
                sa.DateTime(timezone=True),
                server_default=sa.text("now()"),
                nullable=False,
            ),
        )


def downgrade():
    op.drop_column("paragraph_outcomes", "updated_at")
