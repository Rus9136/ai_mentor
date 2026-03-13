"""Add content-linking columns (school, subject, textbook, paragraph) to daily_quests,
replace unique constraint with school-scoped index, update RLS policies and grants.

Revision ID: 051_daily_quests_content_linking
Revises: 050_gamification
"""

from alembic import op

revision = '051_daily_quests_content_linking'
down_revision = '050_gamification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── Add content-linking columns to daily_quests ──
    op.execute("""
        ALTER TABLE daily_quests
            ADD COLUMN school_id INTEGER REFERENCES schools(id) ON DELETE CASCADE,
            ADD COLUMN subject_id INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
            ADD COLUMN textbook_id INTEGER REFERENCES textbooks(id) ON DELETE SET NULL,
            ADD COLUMN paragraph_id INTEGER REFERENCES paragraphs(id) ON DELETE SET NULL;
    """)

    # ── Create indexes ──
    op.execute("CREATE INDEX ix_daily_quests_school ON daily_quests(school_id);")
    op.execute("CREATE INDEX ix_daily_quests_subject ON daily_quests(subject_id);")

    # ── Add hierarchy constraint ──
    op.execute("""
        ALTER TABLE daily_quests ADD CONSTRAINT chk_quest_content_hierarchy CHECK (
            (paragraph_id IS NULL OR textbook_id IS NOT NULL)
            AND (textbook_id IS NULL OR subject_id IS NOT NULL)
        );
    """)

    # ── Replace unique constraint on code with school-scoped unique index ──
    op.execute("ALTER TABLE daily_quests DROP CONSTRAINT daily_quests_code_key;")
    op.execute("CREATE UNIQUE INDEX uq_daily_quests_code_school ON daily_quests(code, COALESCE(school_id, 0));")

    # ── Update grants: add INSERT, UPDATE, DELETE (previously only SELECT) ──
    op.execute("GRANT INSERT, UPDATE, DELETE ON daily_quests TO ai_mentor_app;")

    # ── Update RLS policies ──
    # Drop old public-read policy
    op.execute("DROP POLICY daily_quests_public_read ON daily_quests;")

    # SELECT: global quests (school_id IS NULL) visible to all,
    #         school-specific visible to matching school + super_admin
    op.execute("""
        CREATE POLICY daily_quests_select ON daily_quests
        FOR SELECT USING (
            school_id IS NULL
            OR COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # INSERT: super_admin for global (school_id IS NULL), school admin for own school
    op.execute("""
        CREATE POLICY daily_quests_insert ON daily_quests
        FOR INSERT WITH CHECK (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # UPDATE: same as INSERT
    op.execute("""
        CREATE POLICY daily_quests_update ON daily_quests
        FOR UPDATE USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # DELETE: same as INSERT
    op.execute("""
        CREATE POLICY daily_quests_delete ON daily_quests
        FOR DELETE USING (
            COALESCE(NULLIF(current_setting('app.is_super_admin', true), ''), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # ── Update alembic_version ──
    op.execute("UPDATE alembic_version SET version_num = '051_daily_quests_content_linking' WHERE version_num = '050_gamification';")


def downgrade() -> None:
    # ── Revert RLS policies ──
    op.execute("DROP POLICY IF EXISTS daily_quests_delete ON daily_quests;")
    op.execute("DROP POLICY IF EXISTS daily_quests_update ON daily_quests;")
    op.execute("DROP POLICY IF EXISTS daily_quests_insert ON daily_quests;")
    op.execute("DROP POLICY IF EXISTS daily_quests_select ON daily_quests;")

    # Restore original public-read policy
    op.execute("""
        CREATE POLICY daily_quests_public_read ON daily_quests
        FOR SELECT USING (true);
    """)

    # ── Revoke added grants ──
    op.execute("REVOKE INSERT, UPDATE, DELETE ON daily_quests FROM ai_mentor_app;")

    # ── Restore original unique constraint ──
    op.execute("DROP INDEX IF EXISTS uq_daily_quests_code_school;")
    op.execute("ALTER TABLE daily_quests ADD CONSTRAINT daily_quests_code_key UNIQUE (code);")

    # ── Drop hierarchy constraint ──
    op.execute("ALTER TABLE daily_quests DROP CONSTRAINT IF EXISTS chk_quest_content_hierarchy;")

    # ── Drop indexes ──
    op.execute("DROP INDEX IF EXISTS ix_daily_quests_subject;")
    op.execute("DROP INDEX IF EXISTS ix_daily_quests_school;")

    # ── Drop content-linking columns ──
    op.execute("""
        ALTER TABLE daily_quests
            DROP COLUMN IF EXISTS paragraph_id,
            DROP COLUMN IF EXISTS textbook_id,
            DROP COLUMN IF EXISTS subject_id,
            DROP COLUMN IF EXISTS school_id;
    """)

    # ── Revert alembic_version ──
    op.execute("UPDATE alembic_version SET version_num = '050_gamification' WHERE version_num = '051_daily_quests_content_linking';")
