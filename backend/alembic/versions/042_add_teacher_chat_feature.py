"""Add teacher_chat value to llm_feature enum.

Revision ID: 042_add_teacher_chat_feature
Revises: 041_teacher_chat
"""

revision = "042_add_teacher_chat_feature"
down_revision = "041_teacher_chat"

from alembic import op


def upgrade():
    op.execute("ALTER TYPE llm_feature ADD VALUE IF NOT EXISTS 'teacher_chat'")


def downgrade():
    # PostgreSQL does not support removing values from enums.
    pass
