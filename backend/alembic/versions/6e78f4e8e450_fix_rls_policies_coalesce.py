"""fix_rls_policies_coalesce

Revision ID: 6e78f4e8e450
Revises: 013
Create Date: 2025-12-16 11:13:11.215086

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6e78f4e8e450'
down_revision: Union[str, None] = '013'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Fix RLS policies to use COALESCE and NULLIF for proper handling of empty strings.
    
    Problem: current_setting() returns empty string '' when variable is not set,
    and casting '' to integer or boolean causes errors.
    
    Solution: Use COALESCE(current_setting(...), 'false') for booleans
    and COALESCE(NULLIF(current_setting(...), ''), '0')::int for integers.
    """
    
    # ===========================================
    # Fix chapters policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON chapters;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON chapters
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM textbooks
                WHERE textbooks.id = chapters.textbook_id
                AND (
                    textbooks.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                    OR textbooks.school_id IS NULL
                )
            )
        );
    """)
    
    # ===========================================
    # Fix paragraphs policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON paragraphs;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON paragraphs
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM chapters
                JOIN textbooks ON textbooks.id = chapters.textbook_id
                WHERE chapters.id = paragraphs.chapter_id
                AND (
                    textbooks.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                    OR textbooks.school_id IS NULL
                )
            )
        );
    """)
    
    # ===========================================
    # Fix paragraph_embeddings policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON paragraph_embeddings;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON paragraph_embeddings
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM paragraphs
                JOIN chapters ON chapters.id = paragraphs.chapter_id
                JOIN textbooks ON textbooks.id = chapters.textbook_id
                WHERE paragraphs.id = paragraph_embeddings.paragraph_id
                AND (
                    textbooks.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                    OR textbooks.school_id IS NULL
                )
            )
        );
    """)
    
    # ===========================================
    # Fix questions policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON questions;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON questions
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM tests
                WHERE tests.id = questions.test_id
                AND (
                    tests.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                    OR tests.school_id IS NULL
                )
            )
        );
    """)
    
    # ===========================================
    # Fix question_options policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON question_options;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON question_options
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM questions
                JOIN tests ON tests.id = questions.test_id
                WHERE questions.id = question_options.question_id
                AND (
                    tests.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                    OR tests.school_id IS NULL
                )
            )
        );
    """)
    
    # ===========================================
    # Fix progress tables policies
    # ===========================================
    progress_tables = [
        'test_attempts',
        'mastery_history',
        'adaptive_groups',
        'student_paragraphs',
        'learning_sessions',
        'learning_activities',
        'sync_queue',
    ]
    
    for table in progress_tables:
        op.execute(f"""
            DROP POLICY IF EXISTS tenant_isolation_policy ON {table};
        """)
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            TO PUBLIC
            USING (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            );
        """)
        
        op.execute(f"""
            DROP POLICY IF EXISTS tenant_insert_policy ON {table};
        """)
        op.execute(f"""
            CREATE POLICY tenant_insert_policy ON {table}
            FOR INSERT
            TO PUBLIC
            WITH CHECK (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            );
        """)
    
    # ===========================================
    # Fix test_attempt_answers policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempt_answers;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON test_attempt_answers
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM test_attempts
                WHERE test_attempts.id = test_attempt_answers.attempt_id
                AND test_attempts.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)
    
    # ===========================================
    # Fix assignments policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON assignments;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON assignments
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)
    op.execute("""
        DROP POLICY IF EXISTS tenant_insert_policy ON assignments;
    """)
    op.execute("""
        CREATE POLICY tenant_insert_policy ON assignments
        FOR INSERT
        TO PUBLIC
        WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)
    
    # ===========================================
    # Fix assignment_tests policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON assignment_tests;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON assignment_tests
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM assignments
                WHERE assignments.id = assignment_tests.assignment_id
                AND assignments.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)
    
    # ===========================================
    # Fix student_assignments policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON student_assignments;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON student_assignments
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM assignments
                WHERE assignments.id = student_assignments.assignment_id
                AND assignments.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)
    
    # ===========================================
    # Fix parent_students policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON parent_students;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON parent_students
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM parents
                WHERE parents.id = parent_students.parent_id
                AND parents.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)
    
    # ===========================================
    # Fix class_students policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON class_students;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON class_students
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM school_classes
                WHERE school_classes.id = class_students.class_id
                AND school_classes.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)
    
    # ===========================================
    # Fix class_teachers policy
    # ===========================================
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON class_teachers;
    """)
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON class_teachers
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM school_classes
                WHERE school_classes.id = class_teachers.class_id
                AND school_classes.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)


def downgrade() -> None:
    """
    Revert to old RLS policies (not recommended, as they have bugs).
    """
    # This downgrade is intentionally minimal - reverting would reintroduce bugs
    # If needed, manually restore from migration 401bffeccd70_enable_rls_policies.py
    pass
