"""LLM usage logs for token monitoring.

Revision ID: 039_llm_usage_logs
Revises: 038_lesson_plans
"""
from alembic import op
import sqlalchemy as sa

revision = '039_llm_usage_logs'
down_revision = '038_lesson_plans'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type
    op.execute("""
        CREATE TYPE llm_feature AS ENUM (
            'chat', 'rag', 'lesson_plan',
            'homework_generation', 'homework_grading',
            'audio_text', 'memory', 'system'
        )
    """)

    # Create table
    op.execute("""
        CREATE TABLE llm_usage_logs (
            id SERIAL PRIMARY KEY,
            user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL,
            student_id INTEGER REFERENCES students(id) ON DELETE SET NULL,
            teacher_id INTEGER REFERENCES teachers(id) ON DELETE SET NULL,
            feature llm_feature NOT NULL,
            provider VARCHAR(50) NOT NULL,
            model VARCHAR(100) NOT NULL,
            prompt_tokens INTEGER,
            completion_tokens INTEGER,
            total_tokens INTEGER,
            latency_ms INTEGER,
            success BOOLEAN NOT NULL DEFAULT true,
            error_message TEXT,
            estimated_cost_usd DOUBLE PRECISION,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)

    # Indexes
    op.execute("CREATE INDEX ix_llm_usage_logs_user_id ON llm_usage_logs (user_id)")
    op.execute("CREATE INDEX ix_llm_usage_logs_school_id ON llm_usage_logs (school_id)")
    op.execute("CREATE INDEX ix_llm_usage_logs_feature ON llm_usage_logs (feature)")
    op.execute("CREATE INDEX ix_llm_usage_logs_created_at ON llm_usage_logs (created_at)")
    op.execute("CREATE INDEX ix_llm_usage_logs_school_created ON llm_usage_logs (school_id, created_at)")

    # Grants
    op.execute("GRANT SELECT, INSERT, UPDATE ON llm_usage_logs TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE llm_usage_logs_id_seq TO ai_mentor_app")

    # RLS
    op.execute("ALTER TABLE llm_usage_logs ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY llm_usage_logs_school_isolation ON llm_usage_logs
        FOR ALL
        USING (
            NULLIF(current_setting('app.current_school_id', true), '') IS NULL
            OR school_id IS NULL
            OR school_id = NULLIF(current_setting('app.current_school_id', true), '')::INTEGER
        )
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS llm_usage_logs_school_isolation ON llm_usage_logs")
    op.execute("DROP TABLE IF EXISTS llm_usage_logs")
    op.execute("DROP TYPE IF EXISTS llm_feature")
