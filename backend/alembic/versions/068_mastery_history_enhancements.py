"""
Enhance mastery_history table for full progress tracking.

Changes:
- Add source_type column (diagnostic/formative/summative/self_assessment/practice)
- Add score_delta for trend analysis
- Add best_score_at_time and attempts_count_at_time snapshots
- Add composite indexes for timeline queries
- Now records EVERY mastery change, not just level/status transitions

Revision ID: 068_mastery_history_enhancements
Revises: 067_fix_rls_super_admin_bypass
"""
revision = "068_mastery_history_enhancements"
down_revision = "067_fix_rls_super_admin_bypass"

from alembic import op


def upgrade() -> None:
    # 1. Add new columns
    op.execute("""
        ALTER TABLE mastery_history
            ADD COLUMN IF NOT EXISTS source_type VARCHAR(30) DEFAULT 'formative',
            ADD COLUMN IF NOT EXISTS score_delta FLOAT,
            ADD COLUMN IF NOT EXISTS best_score_at_time FLOAT,
            ADD COLUMN IF NOT EXISTS attempts_count_at_time INTEGER;
    """)

    # 2. Backfill existing rows
    op.execute("""
        UPDATE mastery_history SET source_type = 'formative' WHERE source_type IS NULL;
    """)

    # 3. Make source_type NOT NULL
    op.execute("""
        ALTER TABLE mastery_history ALTER COLUMN source_type SET NOT NULL;
    """)

    # 4. Indexes for timeline queries
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mastery_history_source_type
            ON mastery_history(source_type);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mastery_history_student_para_time
            ON mastery_history(student_id, paragraph_id, recorded_at DESC);
    """)
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_mastery_history_student_chapter_time
            ON mastery_history(student_id, chapter_id, recorded_at DESC)
            WHERE chapter_id IS NOT NULL;
    """)

    # 5. Ensure grants
    op.execute("""
        GRANT SELECT, INSERT, UPDATE ON mastery_history TO ai_mentor_app;
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_mastery_history_student_chapter_time;")
    op.execute("DROP INDEX IF EXISTS ix_mastery_history_student_para_time;")
    op.execute("DROP INDEX IF EXISTS ix_mastery_history_source_type;")
    op.execute("""
        ALTER TABLE mastery_history
            DROP COLUMN IF EXISTS source_type,
            DROP COLUMN IF EXISTS score_delta,
            DROP COLUMN IF EXISTS best_score_at_time,
            DROP COLUMN IF EXISTS attempts_count_at_time;
    """)
