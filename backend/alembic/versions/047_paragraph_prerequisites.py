"""Add paragraph_prerequisites table for Knowledge Graph.

Revision ID: 047_paragraph_prerequisites
Revises: 046_metacognitive_pattern
"""

from alembic import op

revision = '047_paragraph_prerequisites'
down_revision = '046_metacognitive_pattern'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE paragraph_prerequisites (
            id SERIAL PRIMARY KEY,
            paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
            prerequisite_paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
            strength VARCHAR(10) NOT NULL DEFAULT 'required',

            -- Timestamps
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            UNIQUE(paragraph_id, prerequisite_paragraph_id),
            CHECK(paragraph_id != prerequisite_paragraph_id),
            CHECK(strength IN ('required', 'recommended'))
        );
    """)

    # Indexes
    op.execute("CREATE INDEX idx_prereq_paragraph_id ON paragraph_prerequisites(paragraph_id);")
    op.execute("CREATE INDEX idx_prereq_prerequisite_id ON paragraph_prerequisites(prerequisite_paragraph_id);")

    # Grants for runtime user (DELETE needed for SUPER_ADMIN to remove links)
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON paragraph_prerequisites TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE paragraph_prerequisites_id_seq TO ai_mentor_app;")

    # No RLS — prerequisites are global content (no school_id), managed by SUPER_ADMIN only


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS paragraph_prerequisites;")
