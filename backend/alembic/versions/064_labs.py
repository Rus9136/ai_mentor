"""Create lab tables: labs, lab_progress, lab_tasks, lab_task_answers.

Interactive laboratory experiments for students.

Revision ID: 064_labs
Revises: 063_achievement_xp_source
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision = "064_labs"
down_revision = "063_achievement_xp_source"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- labs ---
    op.create_table(
        "labs",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("subject_id", sa.Integer(), sa.ForeignKey("subjects.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("textbook_id", sa.Integer(), sa.ForeignKey("textbooks.id", ondelete="SET NULL"), nullable=True, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("lab_type", sa.String(50), nullable=False),
        sa.Column("config", JSONB, nullable=False, server_default="{}"),
        sa.Column("content_path", sa.String(500), nullable=True),
        sa.Column("thumbnail_url", sa.String(500), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=True, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- lab_progress ---
    op.create_table(
        "lab_progress",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("progress_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "lab_id", name="uq_lab_progress_student_lab"),
    )

    # --- lab_tasks ---
    op.create_table(
        "lab_tasks",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("lab_id", sa.Integer(), sa.ForeignKey("labs.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("task_type", sa.String(50), nullable=False),
        sa.Column("task_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("xp_reward", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("order_index", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("paragraph_id", sa.Integer(), sa.ForeignKey("paragraphs.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # --- lab_task_answers ---
    op.create_table(
        "lab_task_answers",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("student_id", sa.Integer(), sa.ForeignKey("students.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("lab_task_id", sa.Integer(), sa.ForeignKey("lab_tasks.id", ondelete="CASCADE"), nullable=False, index=True),
        sa.Column("answer_data", JSONB, nullable=False, server_default="{}"),
        sa.Column("is_correct", sa.Boolean(), nullable=False),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("answered_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("student_id", "lab_task_id", name="uq_lab_task_answer_student_task"),
    )

    # --- Grants for ai_mentor_app (runtime user) ---
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON labs TO ai_mentor_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON lab_progress TO ai_mentor_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON lab_tasks TO ai_mentor_app")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON lab_task_answers TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE labs_id_seq TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE lab_progress_id_seq TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE lab_tasks_id_seq TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE lab_task_answers_id_seq TO ai_mentor_app")


def downgrade() -> None:
    op.drop_table("lab_task_answers")
    op.drop_table("lab_tasks")
    op.drop_table("lab_progress")
    op.drop_table("labs")
