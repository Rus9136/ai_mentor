"""Fix RLS policies for student onboarding and content access.

Comprehensive RLS fixes for:
- invitation_codes, schools, school_classes: allow SELECT for code validation
- users: allow self-update for onboarding
- students: allow self-registration during onboarding
- textbooks, chapters, paragraphs: allow SELECT for global content (school_id IS NULL)

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2025-12-19 10:30:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Fix RLS policies for onboarding and content access."""

    # === INVITATION_CODES ===
    op.execute("DROP POLICY IF EXISTS invitation_codes_select_policy ON invitation_codes;")
    op.execute("CREATE POLICY invitation_codes_select_policy ON invitation_codes FOR SELECT USING (true);")

    # === SCHOOLS ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON schools;")
    op.execute("CREATE POLICY schools_select_policy ON schools FOR SELECT USING (true);")
    op.execute("""
        CREATE POLICY schools_modify_policy ON schools FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer))
        WITH CHECK ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)

    # === SCHOOL_CLASSES ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON school_classes;")
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON school_classes;")
    op.execute("CREATE POLICY school_classes_select_policy ON school_classes FOR SELECT USING (true);")
    op.execute("""
        CREATE POLICY school_classes_modify_policy ON school_classes FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer))
        WITH CHECK ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)

    # === USERS ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON users;")
    op.execute("""
        CREATE POLICY users_update_policy ON users FOR UPDATE
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0')::integer)
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY users_delete_policy ON users FOR DELETE
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)

    # === STUDENTS ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON students;")
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON students;")
    op.execute("""
        CREATE POLICY students_select_policy ON students FOR SELECT
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
            OR (user_id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY students_insert_policy ON students FOR INSERT
        WITH CHECK ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)
            OR (user_id = COALESCE(NULLIF(current_setting('app.current_user_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY students_modify_policy ON students FOR UPDATE
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY students_delete_policy ON students FOR DELETE
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)

    # === TEXTBOOKS ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON textbooks;")
    op.execute("DROP POLICY IF EXISTS tenant_insert_policy ON textbooks;")
    op.execute("""
        CREATE POLICY textbooks_select_policy ON textbooks FOR SELECT
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id IS NULL)
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY textbooks_modify_policy ON textbooks FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer))
        WITH CHECK ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)

    # === CHAPTERS ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON chapters;")
    op.execute("""
        CREATE POLICY chapters_select_policy ON chapters FOR SELECT
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR EXISTS (SELECT 1 FROM textbooks t WHERE t.id = chapters.textbook_id
                AND (t.school_id IS NULL OR t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)));
    """)
    op.execute("""
        CREATE POLICY chapters_modify_policy ON chapters FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR EXISTS (SELECT 1 FROM textbooks t WHERE t.id = chapters.textbook_id
                AND t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer))
        WITH CHECK ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR EXISTS (SELECT 1 FROM textbooks t WHERE t.id = chapters.textbook_id
                AND t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)

    # === PARAGRAPHS ===
    op.execute("DROP POLICY IF EXISTS tenant_isolation_policy ON paragraphs;")
    op.execute("""
        CREATE POLICY paragraphs_select_policy ON paragraphs FOR SELECT
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR EXISTS (SELECT 1 FROM chapters c JOIN textbooks t ON t.id = c.textbook_id
                WHERE c.id = paragraphs.chapter_id
                AND (t.school_id IS NULL OR t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer)));
    """)
    op.execute("""
        CREATE POLICY paragraphs_modify_policy ON paragraphs FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR EXISTS (SELECT 1 FROM chapters c JOIN textbooks t ON t.id = c.textbook_id
                WHERE c.id = paragraphs.chapter_id
                AND t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer))
        WITH CHECK ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR EXISTS (SELECT 1 FROM chapters c JOIN textbooks t ON t.id = c.textbook_id
                WHERE c.id = paragraphs.chapter_id
                AND t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)


def downgrade() -> None:
    """Restore original tenant isolation policies."""
    # Simplified - just restore basic tenant_isolation_policy for each table
    tables = ['invitation_codes', 'schools', 'school_classes', 'users', 'students', 'textbooks', 'chapters', 'paragraphs']

    for table in tables:
        # Drop all new policies
        for policy in ['select_policy', 'modify_policy', 'insert_policy', 'update_policy', 'delete_policy']:
            op.execute(f"DROP POLICY IF EXISTS {table}_{policy} ON {table};")
            op.execute(f"DROP POLICY IF EXISTS {table.rstrip('s')}s_{policy} ON {table};")

    # Restore basic policies
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON invitation_codes FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON schools FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON school_classes FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON users FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON students FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON textbooks FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true')
            OR (school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON chapters FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'));
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON paragraphs FOR ALL
        USING ((COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'));
    """)
