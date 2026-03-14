"""Add quiz battle tables: quiz_sessions, quiz_participants, quiz_answers.

Revision ID: 051_quiz_sessions
Revises: 050_gamification
"""

from alembic import op

revision = '052_quiz_sessions'
down_revision = '051_daily_quests_content_linking'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Extend xp_source_type enum ──
    op.execute("ALTER TYPE xp_source_type ADD VALUE IF NOT EXISTS 'quiz_battle';")

    # ── quiz_session_status enum ──
    op.execute("""
        CREATE TYPE quiz_session_status AS ENUM ('lobby', 'in_progress', 'finished', 'cancelled');
    """)

    # ── quiz_sessions ──
    op.execute("""
        CREATE TABLE quiz_sessions (
            id SERIAL PRIMARY KEY,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            class_id INTEGER REFERENCES school_classes(id) ON DELETE SET NULL,
            test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
            join_code VARCHAR(6) NOT NULL,
            status quiz_session_status NOT NULL DEFAULT 'lobby',
            settings JSONB NOT NULL DEFAULT '{}',
            question_count INTEGER NOT NULL DEFAULT 0,
            current_question_index INTEGER NOT NULL DEFAULT -1,
            started_at TIMESTAMPTZ,
            finished_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uix_quiz_sessions_join_code UNIQUE (join_code)
        );
    """)
    op.execute("CREATE INDEX ix_quiz_sessions_school ON quiz_sessions(school_id);")
    op.execute("CREATE INDEX ix_quiz_sessions_teacher ON quiz_sessions(teacher_id);")
    op.execute("CREATE INDEX ix_quiz_sessions_join_code ON quiz_sessions(join_code);")
    op.execute("""
        CREATE INDEX ix_quiz_sessions_active ON quiz_sessions(status)
        WHERE status IN ('lobby', 'in_progress');
    """)

    # ── quiz_participants ──
    op.execute("""
        CREATE TABLE quiz_participants (
            id SERIAL PRIMARY KEY,
            quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            total_score INTEGER NOT NULL DEFAULT 0,
            correct_answers INTEGER NOT NULL DEFAULT 0,
            rank INTEGER,
            xp_earned INTEGER NOT NULL DEFAULT 0,
            joined_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            finished_at TIMESTAMPTZ,
            CONSTRAINT uix_quiz_participant UNIQUE (quiz_session_id, student_id)
        );
    """)
    op.execute("CREATE INDEX ix_quiz_participants_school ON quiz_participants(school_id);")
    op.execute("CREATE INDEX ix_quiz_participants_session ON quiz_participants(quiz_session_id);")

    # ── quiz_answers ──
    op.execute("""
        CREATE TABLE quiz_answers (
            id SERIAL PRIMARY KEY,
            quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            participant_id INTEGER NOT NULL REFERENCES quiz_participants(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            question_index INTEGER NOT NULL,
            selected_option INTEGER NOT NULL,
            is_correct BOOLEAN NOT NULL,
            answer_time_ms INTEGER NOT NULL,
            score INTEGER NOT NULL DEFAULT 0,
            answered_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uix_quiz_answer UNIQUE (participant_id, question_index)
        );
    """)
    op.execute("CREATE INDEX ix_quiz_answers_school ON quiz_answers(school_id);")
    op.execute("CREATE INDEX ix_quiz_answers_session_question ON quiz_answers(quiz_session_id, question_index);")

    # ── GRANTS ──
    op.execute("GRANT SELECT, INSERT, UPDATE ON quiz_sessions TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE quiz_sessions_id_seq TO ai_mentor_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE ON quiz_participants TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE quiz_participants_id_seq TO ai_mentor_app;")
    op.execute("GRANT SELECT, INSERT, UPDATE ON quiz_answers TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE quiz_answers_id_seq TO ai_mentor_app;")

    # ── RLS ──
    rls_using = """
        COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
        OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
    """

    for table in ('quiz_sessions', 'quiz_participants', 'quiz_answers'):
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"""
            CREATE POLICY {table}_tenant_isolation ON {table}
            FOR ALL USING ({rls_using});
        """)

    # ── Update alembic version ──
    op.execute(
        "UPDATE alembic_version SET version_num = '052_quiz_sessions' "
        "WHERE version_num = '051_daily_quests_content_linking';"
    )


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS quiz_answers;")
    op.execute("DROP TABLE IF EXISTS quiz_participants;")
    op.execute("DROP TABLE IF EXISTS quiz_sessions;")
    op.execute("DROP TYPE IF EXISTS quiz_session_status;")
    # Note: cannot remove enum value from xp_source_type in PostgreSQL
