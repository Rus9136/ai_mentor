"""Create lesson_plans table for storing generated QMJ plans.

Revision ID: 038_lesson_plans
Revises: 037_outcomes_updated_at
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "038_lesson_plans"
down_revision = "037_outcomes_updated_at"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "lesson_plans",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paragraph_id", sa.Integer(), sa.ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("language", sa.String(2), nullable=False, server_default="kk"),
        sa.Column("duration_min", sa.Integer(), nullable=False, server_default="40"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("plan_data", JSONB, nullable=False),
        sa.Column("context_data", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_lesson_plans_teacher_id", "lesson_plans", ["teacher_id"])
    op.create_index("ix_lesson_plans_paragraph_id", "lesson_plans", ["paragraph_id"])
    op.create_index("ix_lesson_plans_school_id", "lesson_plans", ["school_id"])

    # RLS policies
    op.execute("""
        ALTER TABLE lesson_plans ENABLE ROW LEVEL SECURITY;
        ALTER TABLE lesson_plans FORCE ROW LEVEL SECURITY;

        CREATE POLICY lesson_plans_read_policy ON lesson_plans FOR SELECT USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );

        CREATE POLICY lesson_plans_write_policy ON lesson_plans USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        ) WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );

        GRANT SELECT, INSERT, UPDATE, DELETE ON lesson_plans TO ai_mentor_app;
        GRANT USAGE, SELECT ON SEQUENCE lesson_plans_id_seq TO ai_mentor_app;
    """)


def downgrade():
    op.drop_table("lesson_plans")
