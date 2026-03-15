"""Add power-ups table, powerup_used/confidence_mode columns on quiz_answers.

Supports Phase 2.4: Power-ups and Confidence Mode.

Revision ID: 060_quiz_powerups
Revises: 059_short_answer_and_exit_ticket
"""

from alembic import op


revision = "060_quiz_powerups"
down_revision = "059_short_answer_and_exit_ticket"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Power-ups table ──
    op.execute("""
        CREATE TABLE quiz_participant_powerups (
            id SERIAL PRIMARY KEY,
            quiz_session_id INTEGER NOT NULL REFERENCES quiz_sessions(id) ON DELETE CASCADE,
            participant_id INTEGER NOT NULL REFERENCES quiz_participants(id) ON DELETE CASCADE,
            school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
            powerup_type VARCHAR(20) NOT NULL,
            question_index INTEGER NOT NULL,
            xp_cost INTEGER NOT NULL,
            activated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            applied BOOLEAN NOT NULL DEFAULT FALSE,
            CONSTRAINT uix_powerup_per_question UNIQUE (participant_id, question_index),
            CONSTRAINT chk_powerup_type CHECK (
                powerup_type IN ('double_points', 'fifty_fifty', 'time_freeze', 'shield')
            )
        );
    """)

    op.execute("""
        CREATE INDEX idx_powerup_participant
        ON quiz_participant_powerups(participant_id, question_index);
    """)

    # ── RLS ──
    op.execute("ALTER TABLE quiz_participant_powerups ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY quiz_powerups_school_policy ON quiz_participant_powerups
        USING (school_id = current_setting('app.school_id', true)::int);
    """)

    # ── GRANTS ──
    op.execute("GRANT SELECT, INSERT, UPDATE ON quiz_participant_powerups TO ai_mentor_app;")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE quiz_participant_powerups_id_seq TO ai_mentor_app;")

    # ── New columns on quiz_answers ──
    op.execute("ALTER TABLE quiz_answers ADD COLUMN powerup_used VARCHAR(20) DEFAULT NULL;")
    op.execute("ALTER TABLE quiz_answers ADD COLUMN confidence_mode VARCHAR(10) DEFAULT NULL;")

    # ── New XP source types ──
    op.execute("ALTER TYPE xp_source_type ADD VALUE IF NOT EXISTS 'powerup_purchase';")
    op.execute("ALTER TYPE xp_source_type ADD VALUE IF NOT EXISTS 'weekly_tournament';")


def downgrade() -> None:
    op.execute("ALTER TABLE quiz_answers DROP COLUMN IF EXISTS confidence_mode;")
    op.execute("ALTER TABLE quiz_answers DROP COLUMN IF EXISTS powerup_used;")
    op.execute("DROP TABLE IF EXISTS quiz_participant_powerups CASCADE;")
