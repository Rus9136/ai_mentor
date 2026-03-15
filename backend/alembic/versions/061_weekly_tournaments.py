"""Add weekly tournament table.

Supports Phase 2.4: Automated weekly quiz tournaments.

Revision ID: 061_weekly_tournaments
Revises: 060_quiz_powerups
"""

from alembic import op


revision = "061_weekly_tournaments"
down_revision = "060_quiz_powerups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE quiz_tournaments (
            id SERIAL PRIMARY KEY,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            class_id INTEGER NOT NULL REFERENCES school_classes(id) ON DELETE CASCADE,
            quiz_session_id INTEGER REFERENCES quiz_sessions(id) ON DELETE SET NULL,
            week_start DATE NOT NULL,
            week_end DATE NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'scheduled',
            xp_rank_1 INTEGER NOT NULL DEFAULT 100,
            xp_rank_2 INTEGER NOT NULL DEFAULT 75,
            xp_rank_3 INTEGER NOT NULL DEFAULT 50,
            xp_participation INTEGER NOT NULL DEFAULT 25,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uix_tournament_class_week UNIQUE (class_id, week_start),
            CONSTRAINT chk_tournament_status CHECK (
                status IN ('scheduled', 'active', 'finished', 'cancelled')
            )
        );
    """)

    op.execute("CREATE INDEX idx_tournament_school ON quiz_tournaments(school_id);")
    op.execute("CREATE INDEX idx_tournament_status ON quiz_tournaments(status);")

    # RLS
    op.execute("ALTER TABLE quiz_tournaments ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY quiz_tournaments_school_policy ON quiz_tournaments
        USING (school_id = current_setting('app.school_id', true)::int);
    """)

    # GRANTS
    op.execute("GRANT SELECT, INSERT, UPDATE ON quiz_tournaments TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE quiz_tournaments_id_seq TO ai_mentor_app;")


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS quiz_tournaments CASCADE;")
