"""Add quiz_teams table, team_id to participants, make test_id nullable.

Supports Phase 2.2: Team Mode, Self-Paced, Quick Question.

Revision ID: 058_quiz_teams_and_modes
Revises: 057_quiz_timestamp_columns
"""

from alembic import op

revision = '058_quiz_teams_and_modes'
down_revision = '057_quiz_timestamp_columns'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create quiz_teams table
    op.execute("""
        CREATE TABLE quiz_teams (
            id SERIAL PRIMARY KEY,
            quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            name VARCHAR(50) NOT NULL,
            color VARCHAR(7) NOT NULL,
            total_score INTEGER NOT NULL DEFAULT 0,
            correct_answers INTEGER NOT NULL DEFAULT 0,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # Indexes
    op.execute("CREATE INDEX ix_quiz_teams_session ON quiz_teams(quiz_session_id);")
    op.execute("CREATE INDEX ix_quiz_teams_school ON quiz_teams(school_id);")

    # GRANTS
    op.execute("GRANT SELECT, INSERT, UPDATE ON quiz_teams TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE quiz_teams_id_seq TO ai_mentor_app;")

    # RLS
    op.execute("ALTER TABLE quiz_teams ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY quiz_teams_tenant_isolation ON quiz_teams
        FOR ALL USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # 2. Add team_id to quiz_participants
    op.execute("""
        ALTER TABLE quiz_participants
        ADD COLUMN team_id INTEGER REFERENCES quiz_teams(id) ON DELETE SET NULL;
    """)
    op.execute("CREATE INDEX ix_quiz_participants_team ON quiz_participants(team_id);")

    # 3. Make test_id nullable (for Quick Question mode)
    op.execute("ALTER TABLE quiz_sessions ALTER COLUMN test_id DROP NOT NULL;")

    # Update alembic version
    op.execute("""
        UPDATE alembic_version
        SET version_num = '058_quiz_teams_and_modes'
        WHERE version_num = '057_quiz_timestamp_columns';
    """)


def downgrade() -> None:
    # Restore test_id NOT NULL (set any NULLs first)
    op.execute("DELETE FROM quiz_sessions WHERE test_id IS NULL;")
    op.execute("ALTER TABLE quiz_sessions ALTER COLUMN test_id SET NOT NULL;")

    # Drop team_id from quiz_participants
    op.execute("DROP INDEX IF EXISTS ix_quiz_participants_team;")
    op.execute("ALTER TABLE quiz_participants DROP COLUMN IF EXISTS team_id;")

    # Drop quiz_teams table
    op.execute("DROP POLICY IF EXISTS quiz_teams_tenant_isolation ON quiz_teams;")
    op.execute("DROP TABLE IF EXISTS quiz_teams;")

    op.execute("""
        UPDATE alembic_version
        SET version_num = '057_quiz_timestamp_columns'
        WHERE version_num = '058_quiz_teams_and_modes';
    """)
