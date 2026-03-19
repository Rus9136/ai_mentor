"""Create coding challenges tables.

Revision ID: 065_coding_challenges
Revises: 064_labs
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

revision = "065_coding_challenges"
down_revision = "064_labs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ------------------------------------------------------------------
    # coding_topics
    # ------------------------------------------------------------------
    op.create_table(
        "coding_topics",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("title_kk", sa.String(200), nullable=True),
        sa.Column("slug", sa.String(50), nullable=False, unique=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("description_kk", sa.Text(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("icon", sa.String(50), nullable=True),
        sa.Column("grade_level", sa.Integer(), nullable=True),
        sa.Column(
            "paragraph_id",
            sa.Integer(),
            sa.ForeignKey("paragraphs.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("idx_coding_topics_slug", "coding_topics", ["slug"])

    # ------------------------------------------------------------------
    # coding_challenges
    # ------------------------------------------------------------------
    op.create_table(
        "coding_challenges",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "topic_id",
            sa.Integer(),
            sa.ForeignKey("coding_topics.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("title", sa.String(300), nullable=False),
        sa.Column("title_kk", sa.String(300), nullable=True),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("description_kk", sa.Text(), nullable=True),
        sa.Column(
            "difficulty",
            sa.String(20),
            nullable=False,
            server_default="easy",
        ),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("points", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("starter_code", sa.Text(), nullable=True),
        sa.Column("solution_code", sa.Text(), nullable=True),
        sa.Column("hints", JSONB, nullable=False, server_default="'[]'::jsonb"),
        sa.Column("hints_kk", JSONB, nullable=False, server_default="'[]'::jsonb"),
        sa.Column("test_cases", JSONB, nullable=False),
        sa.Column("time_limit_ms", sa.Integer(), nullable=True, server_default="5000"),
        sa.Column(
            "is_active",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "difficulty IN ('easy', 'medium', 'hard')",
            name="ck_coding_challenge_difficulty",
        ),
        sa.CheckConstraint("points > 0", name="ck_coding_challenge_points"),
    )
    op.create_index(
        "idx_coding_challenges_topic_sort",
        "coding_challenges",
        ["topic_id", "sort_order"],
    )

    # ------------------------------------------------------------------
    # coding_submissions
    # ------------------------------------------------------------------
    op.create_table(
        "coding_submissions",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column(
            "student_id",
            sa.Integer(),
            sa.ForeignKey("students.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "school_id",
            sa.Integer(),
            sa.ForeignKey("schools.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "challenge_id",
            sa.Integer(),
            sa.ForeignKey("coding_challenges.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("code", sa.Text(), nullable=False),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("tests_passed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("tests_total", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("execution_time_ms", sa.Integer(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("xp_earned", sa.Integer(), nullable=False, server_default="0"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.CheckConstraint(
            "status IN ('passed', 'failed', 'error', 'timeout')",
            name="ck_coding_submission_status",
        ),
    )
    op.create_index(
        "idx_coding_submissions_student_challenge",
        "coding_submissions",
        ["student_id", "challenge_id"],
    )
    op.create_index(
        "idx_coding_submissions_school",
        "coding_submissions",
        ["school_id"],
    )

    # ------------------------------------------------------------------
    # Grants for runtime user
    # ------------------------------------------------------------------
    for table in ("coding_topics", "coding_challenges", "coding_submissions"):
        op.execute(
            f"GRANT SELECT, INSERT, UPDATE, DELETE ON {table} TO ai_mentor_app"
        )
        op.execute(
            f"GRANT USAGE, SELECT ON SEQUENCE {table}_id_seq TO ai_mentor_app"
        )


def downgrade() -> None:
    op.drop_table("coding_submissions")
    op.drop_table("coding_challenges")
    op.drop_table("coding_topics")
