"""Teacher memory: session summaries + long-term teacher profile.

Revision ID: 043_teacher_memory
Revises: 042_add_teacher_chat_feature
"""
from alembic import op

revision = '043_teacher_memory'
down_revision = '042_add_teacher_chat_feature'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # --- teacher_chat_session_summaries ---
    op.execute("""
        CREATE TABLE teacher_chat_session_summaries (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            topic VARCHAR(255),
            summary TEXT NOT NULL,
            key_insights JSONB DEFAULT '[]'::jsonb,
            session_type VARCHAR(30),
            message_count INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_teacher_session_summary UNIQUE (session_id)
        )
    """)

    op.execute("CREATE INDEX ix_tcss_teacher_id ON teacher_chat_session_summaries (teacher_id)")
    op.execute("CREATE INDEX ix_tcss_school_id ON teacher_chat_session_summaries (school_id)")
    op.execute("CREATE INDEX ix_tcss_teacher_created ON teacher_chat_session_summaries (teacher_id, created_at DESC)")

    op.execute("GRANT SELECT, INSERT, UPDATE ON teacher_chat_session_summaries TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE teacher_chat_session_summaries_id_seq TO ai_mentor_app")

    op.execute("ALTER TABLE teacher_chat_session_summaries ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tcss_school_isolation ON teacher_chat_session_summaries
        FOR ALL
        USING (
            school_id IS NULL
            OR school_id = current_setting('app.current_school_id', true)::INTEGER
        )
    """)

    # --- teacher_memory ---
    op.execute("""
        CREATE TABLE teacher_memory (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            memory_data JSONB NOT NULL DEFAULT '{}'::jsonb,
            extraction_count INTEGER NOT NULL DEFAULT 0,
            last_session_id INTEGER REFERENCES chat_sessions(id) ON DELETE SET NULL,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            CONSTRAINT uq_teacher_memory UNIQUE (teacher_id)
        )
    """)

    op.execute("CREATE INDEX ix_tm_teacher_id ON teacher_memory (teacher_id)")
    op.execute("CREATE INDEX ix_tm_school_id ON teacher_memory (school_id)")

    op.execute("GRANT SELECT, INSERT, UPDATE ON teacher_memory TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE teacher_memory_id_seq TO ai_mentor_app")

    op.execute("ALTER TABLE teacher_memory ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY tm_school_isolation ON teacher_memory
        FOR ALL
        USING (
            school_id IS NULL
            OR school_id = current_setting('app.current_school_id', true)::INTEGER
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS tm_school_isolation ON teacher_memory")
    op.execute("DROP TABLE IF EXISTS teacher_memory")
    op.execute("DROP POLICY IF EXISTS tcss_school_isolation ON teacher_chat_session_summaries")
    op.execute("DROP TABLE IF EXISTS teacher_chat_session_summaries")
