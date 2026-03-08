"""Student memory: session summaries + long-term learner profile.

Revision ID: 040_student_memory
Revises: 039_llm_usage_logs
"""
from alembic import op

revision = '040_student_memory'
down_revision = '039_llm_usage_logs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Extend llm_feature enum
    op.execute("ALTER TYPE llm_feature ADD VALUE IF NOT EXISTS 'memory'")

    # --- chat_session_summaries ---
    op.execute("""
        CREATE TABLE chat_session_summaries (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            topic VARCHAR(255),
            summary TEXT NOT NULL,
            knowledge_gaps JSONB DEFAULT '[]'::jsonb,
            confidence_level VARCHAR(20),
            message_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_session_summary UNIQUE (session_id)
        )
    """)

    op.execute("CREATE INDEX ix_css_student_id ON chat_session_summaries (student_id)")
    op.execute("CREATE INDEX ix_css_school_id ON chat_session_summaries (school_id)")
    op.execute("CREATE INDEX ix_css_student_created ON chat_session_summaries (student_id, created_at DESC)")

    op.execute("GRANT SELECT, INSERT, UPDATE ON chat_session_summaries TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE chat_session_summaries_id_seq TO ai_mentor_app")

    op.execute("ALTER TABLE chat_session_summaries ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY css_school_isolation ON chat_session_summaries
        FOR ALL
        USING (
            school_id IS NULL
            OR school_id = current_setting('app.current_school_id', true)::INTEGER
        )
    """)

    # --- student_memory ---
    op.execute("""
        CREATE TABLE student_memory (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            memory_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            extraction_count INTEGER NOT NULL DEFAULT 0,
            last_session_id INTEGER REFERENCES chat_sessions(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_student_memory UNIQUE (student_id)
        )
    """)

    op.execute("CREATE INDEX ix_sm_student_id ON student_memory (student_id)")
    op.execute("CREATE INDEX ix_sm_school_id ON student_memory (school_id)")

    op.execute("GRANT SELECT, INSERT, UPDATE ON student_memory TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE student_memory_id_seq TO ai_mentor_app")

    op.execute("ALTER TABLE student_memory ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY sm_school_isolation ON student_memory
        FOR ALL
        USING (
            school_id IS NULL
            OR school_id = current_setting('app.current_school_id', true)::INTEGER
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS sm_school_isolation ON student_memory")
    op.execute("DROP TABLE IF EXISTS student_memory")
    op.execute("DROP POLICY IF EXISTS css_school_isolation ON chat_session_summaries")
    op.execute("DROP TABLE IF EXISTS chat_session_summaries")
