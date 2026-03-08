"""Add teacher_id to chat_sessions for teacher AI chat.

Revision ID: 041_teacher_chat
Revises: 040_student_memory
"""

revision = "041_teacher_chat"
down_revision = "040_student_memory"

from alembic import op
import sqlalchemy as sa


def upgrade():
    # 1. Add teacher_id column (nullable FK to teachers.id)
    op.add_column(
        "chat_sessions",
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=True),
    )

    # 2. Make student_id nullable (currently NOT NULL)
    op.alter_column("chat_sessions", "student_id", existing_type=sa.Integer(), nullable=True)

    # 3. Add CHECK constraint: at least one of student_id or teacher_id must be set
    op.create_check_constraint(
        "ck_chat_sessions_owner",
        "chat_sessions",
        "student_id IS NOT NULL OR teacher_id IS NOT NULL",
    )

    # 4. Add index on teacher_id
    op.create_index("ix_chat_sessions_teacher_id", "chat_sessions", ["teacher_id"])


def downgrade():
    op.drop_index("ix_chat_sessions_teacher_id", table_name="chat_sessions")
    op.drop_constraint("ck_chat_sessions_owner", "chat_sessions", type_="check")
    op.alter_column("chat_sessions", "student_id", existing_type=sa.Integer(), nullable=False)
    op.drop_column("chat_sessions", "teacher_id")
