"""Add text_answer to quiz_answers, paragraph_id to quiz_sessions.

Supports Phase 2.3: Short Answer questions, Exit Ticket integration.

Revision ID: 059_short_answer_and_exit_ticket
Revises: 058_quiz_teams_and_modes
"""

from alembic import op

revision = '059_short_answer_and_exit_ticket'
down_revision = '058_quiz_teams_and_modes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Add text_answer column to quiz_answers (for short_answer question type)
    op.execute("ALTER TABLE quiz_answers ADD COLUMN text_answer TEXT;")

    # 2. Add paragraph_id to quiz_sessions (for exit ticket -> self-assessment link)
    op.execute("""
        ALTER TABLE quiz_sessions
        ADD COLUMN paragraph_id INTEGER REFERENCES paragraphs(id) ON DELETE SET NULL;
    """)
    op.execute("CREATE INDEX ix_quiz_sessions_paragraph ON quiz_sessions(paragraph_id);")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_quiz_sessions_paragraph;")
    op.execute("ALTER TABLE quiz_sessions DROP COLUMN IF EXISTS paragraph_id;")
    op.execute("ALTER TABLE quiz_answers DROP COLUMN IF EXISTS text_answer;")
