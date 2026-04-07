"""Create presentations table for storing AI-generated PPTX presentations.

Revision ID: 077_presentations
Revises: 076_test_source_clone
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "077_presentations"
down_revision = "076_test_source_clone"
branch_labels = None
depends_on = None


def upgrade():
    # Add 'presentation' value to llm_feature enum
    op.execute("ALTER TYPE llm_feature ADD VALUE IF NOT EXISTS 'presentation'")

    op.create_table(
        "presentations",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("teacher_id", sa.Integer(), sa.ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False),
        sa.Column("school_id", sa.Integer(), sa.ForeignKey("schools.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paragraph_id", sa.Integer(), sa.ForeignKey("paragraphs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("class_id", sa.Integer(), sa.ForeignKey("school_classes.id", ondelete="SET NULL"), nullable=True),
        sa.Column("language", sa.String(2), nullable=False, server_default="kk"),
        sa.Column("slide_count", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("slides_data", JSONB, nullable=False),
        sa.Column("context_data", JSONB, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.create_index("ix_presentations_teacher_id", "presentations", ["teacher_id"])
    op.create_index("ix_presentations_paragraph_id", "presentations", ["paragraph_id"])
    op.create_index("ix_presentations_school_id", "presentations", ["school_id"])

    # RLS policies
    op.execute("""
        ALTER TABLE presentations ENABLE ROW LEVEL SECURITY;
        ALTER TABLE presentations FORCE ROW LEVEL SECURITY;

        CREATE POLICY presentations_read_policy ON presentations FOR SELECT USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );

        CREATE POLICY presentations_write_policy ON presentations USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        ) WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );

        GRANT SELECT, INSERT, UPDATE, DELETE ON presentations TO ai_mentor_app;
        GRANT USAGE, SELECT ON SEQUENCE presentations_id_seq TO ai_mentor_app;
    """)


def downgrade():
    op.drop_table("presentations")
