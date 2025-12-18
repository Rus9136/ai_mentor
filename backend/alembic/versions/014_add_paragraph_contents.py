"""add paragraph_contents table for rich content (explanation, audio, slides, video, cards)

Creates `paragraph_contents` table which stores enriched content for paragraphs
in multiple languages (ru, kk). Each paragraph can have one content record per language.

Content types:
- explain_text: simplified explanation of the paragraph
- audio_url: URL to MP3/OGG/WAV audio file
- slides_url: URL to PDF/PPTX presentation
- video_url: URL to MP4/WEBM video file
- cards: JSONB array of flashcards

RLS strategy (following paragraph_outcomes pattern):
- SELECT: allowed if the linked paragraph is visible for current tenant
  (tenant textbook OR global textbook) OR if app.is_super_admin=true.
- INSERT/UPDATE/DELETE: allowed only for paragraphs that belong to the current tenant
  (textbooks.school_id = current_tenant_id) OR if app.is_super_admin=true.

Revision ID: 014
Revises: 6e78f4e8e450
Create Date: 2025-12-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "014"
down_revision: Union[str, None] = "6e78f4e8e450"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# RLS helper SQL (following established pattern)
IS_SUPER_ADMIN_SQL = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"
CURRENT_TENANT_ID_SQL = "COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int"


def upgrade() -> None:
    # Create paragraph_contents table
    op.create_table(
        "paragraph_contents",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("paragraph_id", sa.Integer(), nullable=False),
        sa.Column("language", sa.String(length=2), nullable=False, server_default="ru"),

        # Content fields
        sa.Column("explain_text", sa.Text(), nullable=True),
        sa.Column("audio_url", sa.Text(), nullable=True),
        sa.Column("slides_url", sa.Text(), nullable=True),
        sa.Column("video_url", sa.Text(), nullable=True),
        sa.Column("cards", postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Metadata
        sa.Column("source_hash", sa.String(length=64), nullable=True),

        # Status fields
        sa.Column("status_explain", sa.String(length=20), nullable=False, server_default="empty"),
        sa.Column("status_audio", sa.String(length=20), nullable=False, server_default="empty"),
        sa.Column("status_slides", sa.String(length=20), nullable=False, server_default="empty"),
        sa.Column("status_video", sa.String(length=20), nullable=False, server_default="empty"),
        sa.Column("status_cards", sa.String(length=20), nullable=False, server_default="empty"),

        # Timestamps
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
            onupdate=sa.func.now(),
            nullable=False,
        ),

        # Constraints
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("paragraph_id", "language", name="uq_paragraph_content_language"),
        sa.CheckConstraint("language IN ('ru', 'kk')", name="chk_paragraph_content_language"),
        sa.ForeignKeyConstraint(
            ["paragraph_id"],
            ["paragraphs.id"],
            ondelete="CASCADE",
            name="fk_paragraph_contents_paragraph",
        ),
    )

    # Create index on paragraph_id for efficient lookups
    op.create_index("ix_paragraph_contents_paragraph_id", "paragraph_contents", ["paragraph_id"])

    # Enable RLS + FORCE
    op.execute("ALTER TABLE paragraph_contents ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE paragraph_contents FORCE ROW LEVEL SECURITY;")

    # Read policy: tenant can read both own + global paragraphs' content
    op.execute(
        f"""
        CREATE POLICY paragraph_contents_read_policy ON paragraph_contents
        FOR SELECT
        TO PUBLIC
        USING (
            {IS_SUPER_ADMIN_SQL}
            OR EXISTS (
                SELECT 1
                FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = paragraph_contents.paragraph_id
                  AND (
                      t.school_id = {CURRENT_TENANT_ID_SQL}
                      OR t.school_id IS NULL
                  )
            )
        );
        """
    )

    # Write policy: tenant can write ONLY for own school paragraphs (not global)
    # SUPER_ADMIN can write for global content (school_id IS NULL)
    op.execute(
        f"""
        CREATE POLICY paragraph_contents_write_policy ON paragraph_contents
        FOR ALL
        TO PUBLIC
        USING (
            {IS_SUPER_ADMIN_SQL}
            OR EXISTS (
                SELECT 1
                FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = paragraph_contents.paragraph_id
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
                WHERE p.id = paragraph_contents.paragraph_id
                  AND t.school_id = {CURRENT_TENANT_ID_SQL}
            )
        );
        """
    )


def downgrade() -> None:
    # Drop RLS policies first
    op.execute("DROP POLICY IF EXISTS paragraph_contents_write_policy ON paragraph_contents;")
    op.execute("DROP POLICY IF EXISTS paragraph_contents_read_policy ON paragraph_contents;")

    # Drop index
    op.drop_index("ix_paragraph_contents_paragraph_id", table_name="paragraph_contents")

    # Drop table
    op.drop_table("paragraph_contents")
