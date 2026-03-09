"""Add review_schedule table for spaced repetition.

Revision ID: 044_review_schedule
Revises: 043_teacher_memory
"""

from alembic import op

revision = '044_review_schedule'
down_revision = '043_teacher_memory'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE review_schedule (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,

            -- Leitner system
            streak INTEGER NOT NULL DEFAULT 0,
            next_review_date DATE NOT NULL,
            last_review_date TIMESTAMPTZ,

            -- Statistics
            total_reviews INTEGER NOT NULL DEFAULT 0,
            successful_reviews INTEGER NOT NULL DEFAULT 0,

            -- Active flag
            is_active BOOLEAN NOT NULL DEFAULT TRUE,

            -- Timestamps
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),

            UNIQUE(student_id, paragraph_id)
        );
    """)

    # Indexes
    op.execute("CREATE INDEX idx_review_schedule_student_id ON review_schedule(student_id);")
    op.execute("CREATE INDEX idx_review_schedule_paragraph_id ON review_schedule(paragraph_id);")
    op.execute("CREATE INDEX idx_review_schedule_school_id ON review_schedule(school_id);")
    op.execute("CREATE INDEX idx_review_schedule_next_review ON review_schedule(next_review_date) WHERE is_active = TRUE;")
    op.execute("CREATE INDEX idx_review_schedule_due ON review_schedule(student_id, next_review_date) WHERE is_active = TRUE;")

    # Grants for runtime user
    op.execute("GRANT SELECT, INSERT, UPDATE ON review_schedule TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE review_schedule_id_seq TO ai_mentor_app;")

    # Row Level Security
    op.execute("ALTER TABLE review_schedule ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY review_schedule_school_isolation ON review_schedule
        USING (school_id = current_setting('app.current_school_id', true)::INTEGER)
        WITH CHECK (school_id = current_setting('app.current_school_id', true)::INTEGER);
    """)


def downgrade() -> None:
    op.execute("DROP POLICY IF EXISTS review_schedule_school_isolation ON review_schedule;")
    op.execute("DROP TABLE IF EXISTS review_schedule;")
