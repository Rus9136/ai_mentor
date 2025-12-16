"""add goso core reference tables (global)

Creates global reference tables for ГОСО:
- subjects
- frameworks
- goso_sections
- goso_subsections
- learning_outcomes

MVP scope:
- No per-school overrides for curriculum_* here (those are Target).
- Tables are GLOBAL (no school_id) and readable by all authenticated users.
- Write access is restricted at DB level to SUPER_ADMIN via session variable:
  `app.is_super_admin = 'true'`.

Revision ID: 012
Revises: c3a8d9e1f0b2
Create Date: 2025-12-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "012"
down_revision: Union[str, None] = "c3a8d9e1f0b2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


IS_SUPER_ADMIN_SQL = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"


def upgrade() -> None:
    # =========================
    # 1) subjects
    # =========================
    op.create_table(
        "subjects",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("name_ru", sa.String(length=255), nullable=False),
        sa.Column("name_kz", sa.String(length=255), nullable=False),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_kz", sa.Text(), nullable=True),
        sa.Column("grade_from", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("grade_to", sa.Integer(), nullable=False, server_default="11"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_subjects_code"),
    )
    op.create_index("ix_subjects_code", "subjects", ["code"])
    op.create_index("ix_subjects_is_active", "subjects", ["is_active"])

    # RLS (global read, super_admin write)
    op.execute("ALTER TABLE subjects ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE subjects FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY subjects_read_policy ON subjects
        FOR SELECT
        TO PUBLIC
        USING (true);
        """
    )
    op.execute(
        f"""
        CREATE POLICY subjects_write_policy ON subjects
        FOR ALL
        TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL});
        """
    )

    # =========================
    # 2) frameworks
    # =========================
    op.create_table(
        "frameworks",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("code", sa.String(length=100), nullable=False),
        sa.Column("subject_id", sa.Integer(), nullable=False),
        sa.Column("title_ru", sa.String(length=500), nullable=False),
        sa.Column("title_kz", sa.String(length=500), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_kz", sa.Text(), nullable=True),
        # Normative fields
        sa.Column("document_type", sa.String(length=255), nullable=True),
        sa.Column("order_number", sa.String(length=50), nullable=True),
        sa.Column("order_date", sa.Date(), nullable=True),
        sa.Column("ministry", sa.String(length=500), nullable=True),
        sa.Column("appendix_number", sa.Integer(), nullable=True),
        sa.Column("amendments", sa.JSON(), nullable=True),
        sa.Column("valid_from", sa.Date(), nullable=True),
        sa.Column("valid_to", sa.Date(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        # Soft delete-ish (align with existing SoftDeleteModel shape)
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code", name="uq_frameworks_code"),
        sa.ForeignKeyConstraint(
            ["subject_id"], ["subjects.id"], ondelete="CASCADE", name="fk_frameworks_subject"
        ),
    )
    op.create_index("ix_frameworks_code", "frameworks", ["code"])
    op.create_index("ix_frameworks_subject_id", "frameworks", ["subject_id"])
    op.create_index("ix_frameworks_is_active", "frameworks", ["is_active"])

    # RLS (global read, super_admin write)
    op.execute("ALTER TABLE frameworks ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE frameworks FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY frameworks_read_policy ON frameworks
        FOR SELECT
        TO PUBLIC
        USING (true);
        """
    )
    op.execute(
        f"""
        CREATE POLICY frameworks_write_policy ON frameworks
        FOR ALL
        TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL});
        """
    )

    # =========================
    # 3) goso_sections
    # =========================
    op.create_table(
        "goso_sections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("framework_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name_ru", sa.String(length=500), nullable=False),
        sa.Column("name_kz", sa.String(length=500), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_kz", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("framework_id", "code", name="uq_goso_sections_framework_code"),
        sa.ForeignKeyConstraint(
            ["framework_id"],
            ["frameworks.id"],
            ondelete="CASCADE",
            name="fk_goso_sections_framework",
        ),
    )
    op.create_index("ix_goso_sections_framework_id", "goso_sections", ["framework_id"])
    op.create_index("ix_goso_sections_display_order", "goso_sections", ["display_order"])

    # RLS (global read, super_admin write)
    op.execute("ALTER TABLE goso_sections ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE goso_sections FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY goso_sections_read_policy ON goso_sections
        FOR SELECT
        TO PUBLIC
        USING (true);
        """
    )
    op.execute(
        f"""
        CREATE POLICY goso_sections_write_policy ON goso_sections
        FOR ALL
        TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL});
        """
    )

    # =========================
    # 4) goso_subsections
    # =========================
    op.create_table(
        "goso_subsections",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("section_id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("name_ru", sa.String(length=500), nullable=False),
        sa.Column("name_kz", sa.String(length=500), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_kz", sa.Text(), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("section_id", "code", name="uq_goso_subsections_section_code"),
        sa.ForeignKeyConstraint(
            ["section_id"],
            ["goso_sections.id"],
            ondelete="CASCADE",
            name="fk_goso_subsections_section",
        ),
    )
    op.create_index("ix_goso_subsections_section_id", "goso_subsections", ["section_id"])
    op.create_index("ix_goso_subsections_display_order", "goso_subsections", ["display_order"])

    # RLS (global read, super_admin write)
    op.execute("ALTER TABLE goso_subsections ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE goso_subsections FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY goso_subsections_read_policy ON goso_subsections
        FOR SELECT
        TO PUBLIC
        USING (true);
        """
    )
    op.execute(
        f"""
        CREATE POLICY goso_subsections_write_policy ON goso_subsections
        FOR ALL
        TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL});
        """
    )

    # =========================
    # 5) learning_outcomes
    # =========================
    op.create_table(
        "learning_outcomes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("framework_id", sa.Integer(), nullable=False),
        sa.Column("subsection_id", sa.Integer(), nullable=False),
        sa.Column(
            "grade",
            sa.Integer(),
            sa.CheckConstraint("grade >= 1 AND grade <= 11", name="ck_learning_outcomes_grade_range"),
            nullable=False,
        ),
        sa.Column("code", sa.String(length=20), nullable=False),
        sa.Column("title_ru", sa.Text(), nullable=False),
        sa.Column("title_kz", sa.Text(), nullable=True),
        sa.Column("description_ru", sa.Text(), nullable=True),
        sa.Column("description_kz", sa.Text(), nullable=True),
        sa.Column("cognitive_level", sa.String(length=50), nullable=True),
        sa.Column("display_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("is_deleted", sa.Boolean(), nullable=False, server_default=sa.text("false")),
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
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("framework_id", "code", name="uq_learning_outcomes_framework_code"),
        sa.ForeignKeyConstraint(
            ["framework_id"],
            ["frameworks.id"],
            ondelete="CASCADE",
            name="fk_learning_outcomes_framework",
        ),
        sa.ForeignKeyConstraint(
            ["subsection_id"],
            ["goso_subsections.id"],
            ondelete="CASCADE",
            name="fk_learning_outcomes_subsection",
        ),
    )
    op.create_index("ix_learning_outcomes_framework_id", "learning_outcomes", ["framework_id"])
    op.create_index("ix_learning_outcomes_subsection_id", "learning_outcomes", ["subsection_id"])
    op.create_index("ix_learning_outcomes_grade", "learning_outcomes", ["grade"])
    op.create_index("ix_learning_outcomes_code", "learning_outcomes", ["code"])
    op.create_index("ix_learning_outcomes_is_active", "learning_outcomes", ["is_active"])

    # RLS (global read, super_admin write)
    op.execute("ALTER TABLE learning_outcomes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE learning_outcomes FORCE ROW LEVEL SECURITY;")
    op.execute(
        """
        CREATE POLICY learning_outcomes_read_policy ON learning_outcomes
        FOR SELECT
        TO PUBLIC
        USING (true);
        """
    )
    op.execute(
        f"""
        CREATE POLICY learning_outcomes_write_policy ON learning_outcomes
        FOR ALL
        TO PUBLIC
        USING ({IS_SUPER_ADMIN_SQL})
        WITH CHECK ({IS_SUPER_ADMIN_SQL});
        """
    )


def downgrade() -> None:
    # Drop in reverse dependency order
    op.drop_index("ix_learning_outcomes_is_active", table_name="learning_outcomes")
    op.drop_index("ix_learning_outcomes_code", table_name="learning_outcomes")
    op.drop_index("ix_learning_outcomes_grade", table_name="learning_outcomes")
    op.drop_index("ix_learning_outcomes_subsection_id", table_name="learning_outcomes")
    op.drop_index("ix_learning_outcomes_framework_id", table_name="learning_outcomes")
    op.drop_table("learning_outcomes")

    op.drop_index("ix_goso_subsections_display_order", table_name="goso_subsections")
    op.drop_index("ix_goso_subsections_section_id", table_name="goso_subsections")
    op.drop_table("goso_subsections")

    op.drop_index("ix_goso_sections_display_order", table_name="goso_sections")
    op.drop_index("ix_goso_sections_framework_id", table_name="goso_sections")
    op.drop_table("goso_sections")

    op.drop_index("ix_frameworks_is_active", table_name="frameworks")
    op.drop_index("ix_frameworks_subject_id", table_name="frameworks")
    op.drop_index("ix_frameworks_code", table_name="frameworks")
    op.drop_table("frameworks")

    op.drop_index("ix_subjects_is_active", table_name="subjects")
    op.drop_index("ix_subjects_code", table_name="subjects")
    op.drop_table("subjects")


