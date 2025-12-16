"""add paragraph_outcomes (paragraph ↔ goso learning outcomes mapping)

Creates `paragraph_outcomes` which links textbook paragraphs to ГОСО learning outcomes.

RLS strategy (critical for multi-tenant safety):
- SELECT: allowed if the linked paragraph is visible for current tenant
  (tenant textbook OR global textbook) OR if app.is_super_admin=true.
- INSERT/UPDATE/DELETE: allowed only for paragraphs that belong to the current tenant
  (textbooks.school_id = current_tenant_id) OR if app.is_super_admin=true.
  This prevents School ADMIN from modifying mappings for GLOBAL content.

Revision ID: 013
Revises: 012
Create Date: 2025-12-12
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "013"
down_revision: Union[str, None] = "012"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


IS_SUPER_ADMIN_SQL = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"
CURRENT_TENANT_ID_SQL = "COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int"


def upgrade() -> None:
    op.create_table(
        "paragraph_outcomes",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("paragraph_id", sa.Integer(), nullable=False),
        sa.Column("outcome_id", sa.Integer(), nullable=False),
        sa.Column("confidence", sa.Numeric(3, 2), nullable=False, server_default="1.0"),
        sa.Column("anchor", sa.String(length=100), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_by", sa.Integer(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paragraph_id", "outcome_id", name="uq_paragraph_outcomes_paragraph_outcome"),
        sa.ForeignKeyConstraint(
            ["paragraph_id"],
            ["paragraphs.id"],
            ondelete="CASCADE",
            name="fk_paragraph_outcomes_paragraph",
        ),
        sa.ForeignKeyConstraint(
            ["outcome_id"],
            ["learning_outcomes.id"],
            ondelete="CASCADE",
            name="fk_paragraph_outcomes_outcome",
        ),
        sa.ForeignKeyConstraint(
            ["created_by"],
            ["users.id"],
            ondelete="SET NULL",
            name="fk_paragraph_outcomes_created_by",
        ),
    )
    op.create_index("ix_paragraph_outcomes_paragraph_id", "paragraph_outcomes", ["paragraph_id"])
    op.create_index("ix_paragraph_outcomes_outcome_id", "paragraph_outcomes", ["outcome_id"])

    # Enable RLS + FORCE
    op.execute("ALTER TABLE paragraph_outcomes ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE paragraph_outcomes FORCE ROW LEVEL SECURITY;")

    # Read policy: tenant can read both own + global paragraphs' mappings
    op.execute(
        f"""
        CREATE POLICY paragraph_outcomes_read_policy ON paragraph_outcomes
        FOR SELECT
        TO PUBLIC
        USING (
            {IS_SUPER_ADMIN_SQL}
            OR EXISTS (
                SELECT 1
                FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = paragraph_outcomes.paragraph_id
                  AND (
                      t.school_id = {CURRENT_TENANT_ID_SQL}
                      OR t.school_id IS NULL
                  )
            )
        );
        """
    )

    # Write policy: tenant can write ONLY for own school paragraphs (not global)
    op.execute(
        f"""
        CREATE POLICY paragraph_outcomes_write_policy ON paragraph_outcomes
        FOR ALL
        TO PUBLIC
        USING (
            {IS_SUPER_ADMIN_SQL}
            OR EXISTS (
                SELECT 1
                FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = paragraph_outcomes.paragraph_id
                  AND t.school_id = {CURRENT_TENANT_ID_SQL}
            )
        )
        WITH CHECK (
            {IS_SUPER_ADMIN_SQL}
            OR EXISTS (
                SELECT 1
                FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = paragraph_outcomes.paragraph_id
                  AND t.school_id = {CURRENT_TENANT_ID_SQL}
            )
        );
        """
    )


def downgrade() -> None:
    op.drop_index("ix_paragraph_outcomes_outcome_id", table_name="paragraph_outcomes")
    op.drop_index("ix_paragraph_outcomes_paragraph_id", table_name="paragraph_outcomes")
    op.drop_table("paragraph_outcomes")


