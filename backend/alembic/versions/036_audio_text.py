"""Add audio_text column to paragraphs table.

Revision ID: 036_audio_text
Revises: 035_textbook_conversions
"""
from alembic import op
import sqlalchemy as sa

revision = "036_audio_text"
down_revision = "035_textbook_conversions"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("paragraphs", sa.Column("audio_text", sa.Text(), nullable=True))


def downgrade():
    op.drop_column("paragraphs", "audio_text")
