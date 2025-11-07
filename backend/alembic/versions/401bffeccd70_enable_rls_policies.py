"""enable_rls_policies

This migration enables Row Level Security (RLS) for all tables with school_id.
RLS provides automatic data isolation at the database level using PostgreSQL session variables.

Key features:
- Tenant isolation: Users only see data from their school (school_id)
- Global content: Content with school_id = NULL is visible to all schools
- SUPER_ADMIN bypass: Database role with BYPASSRLS privilege sees all data

Revision ID: 401bffeccd70
Revises: 9fe5023de6ad
Create Date: 2025-11-06 18:42:57.905869

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '401bffeccd70'
down_revision: Union[str, None] = '9fe5023de6ad'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Enable RLS and create tenant isolation policies for all tables with school_id.
    """

    # ===========================================
    # STEP 1: RLS Strategy
    # ===========================================
    # CRITICAL: RLS requires a non-SUPERUSER database role!
    # - SUPERUSER roles bypass ALL RLS policies
    # - Use 'ai_mentor_app' (non-superuser) role for application connections
    # - Use 'ai_mentor_user' (superuser) only for migrations
    #
    # We use session variables for fine-grained control:
    # - 'app.is_super_admin': Allows SUPER_ADMIN users to see all data
    # - 'app.current_tenant_id': Current school context for regular users
    #
    # IMPORTANT: Policy USING clauses must handle NULL values properly:
    # - COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
    # - COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
    # This prevents cast errors when session variables are not set

    # ===========================================
    # STEP 2A: Schools table (special case)
    # ===========================================
    # Schools table doesn't have school_id, users see only their own school
    # by matching school.id with current_tenant_id

    op.execute("ALTER TABLE schools ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE schools FORCE ROW LEVEL SECURITY;")  # Apply to table owner too
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON schools
        FOR ALL
        TO PUBLIC
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)

    # ===========================================
    # STEP 2B: Basic tenant tables (school_id NOT NULL)
    # ===========================================
    # These tables always have school_id and only show data from current tenant

    basic_tenant_tables = [
        'users',             # Users from same school
        'students',          # Students from same school
        'teachers',          # Teachers from same school
        'parents',           # Parents from same school
        'school_classes',    # Classes from same school
    ]

    for table in basic_tenant_tables:
        # Enable RLS and FORCE it (apply to table owner too)
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Create policy: SUPER_ADMIN sees all, others see only their tenant
        # Use COALESCE to handle NULL/empty session variables
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            TO PUBLIC
            USING (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            );
        """)

        # WITH CHECK ensures new/updated rows belong to current tenant (SUPER_ADMIN can insert anywhere)
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
    # STEP 3: Content tables with direct school_id (nullable - support global content)
    # ===========================================
    # These tables have school_id column that can be NULL (global) or specific value (tenant)

    content_tables_with_school_id = [
        'textbooks',
        'tests',
    ]

    for table in content_tables_with_school_id:
        # Enable RLS and FORCE it
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Create policy: SUPER_ADMIN sees all, others see their tenant + global content
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            TO PUBLIC
            USING (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                OR school_id IS NULL  -- Global content visible to all
            );
        """)

        # WITH CHECK for insert/update
        op.execute(f"""
            CREATE POLICY tenant_insert_policy ON {table}
            FOR INSERT
            TO PUBLIC
            WITH CHECK (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                OR school_id IS NULL
            );
        """)

    # ===========================================
    # STEP 4: Content hierarchy (inherit from textbook)
    # ===========================================
    # chapters, paragraphs, paragraph_embeddings don't have school_id
    # They inherit from textbooks via FK

    # Chapters inherit from textbook
    op.execute("ALTER TABLE chapters ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON chapters
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM textbooks
                WHERE textbooks.id = chapters.textbook_id
                AND (
                    textbooks.school_id = current_setting('app.current_tenant_id', true)::int
                    OR textbooks.school_id IS NULL
                )
            )
        );
    """)

    # Paragraphs inherit from chapter -> textbook
    op.execute("ALTER TABLE paragraphs ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON paragraphs
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM chapters
                JOIN textbooks ON textbooks.id = chapters.textbook_id
                WHERE chapters.id = paragraphs.chapter_id
                AND (
                    textbooks.school_id = current_setting('app.current_tenant_id', true)::int
                    OR textbooks.school_id IS NULL
                )
            )
        );
    """)

    # Paragraph embeddings inherit from paragraph -> chapter -> textbook
    op.execute("ALTER TABLE paragraph_embeddings ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON paragraph_embeddings
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM paragraphs
                JOIN chapters ON chapters.id = paragraphs.chapter_id
                JOIN textbooks ON textbooks.id = chapters.textbook_id
                WHERE paragraphs.id = paragraph_embeddings.paragraph_id
                AND (
                    textbooks.school_id = current_setting('app.current_tenant_id', true)::int
                    OR textbooks.school_id IS NULL
                )
            )
        );
    """)

    # ===========================================
    # STEP 5: Questions and options (inherit from test)
    # ===========================================
    # These don't have direct school_id, so they inherit from test table via JOIN

    # Questions inherit school_id from test
    op.execute("ALTER TABLE questions ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON questions
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM tests
                WHERE tests.id = questions.test_id
                AND (
                    tests.school_id = current_setting('app.current_tenant_id', true)::int
                    OR tests.school_id IS NULL
                )
            )
        );
    """)

    # Question options inherit from question -> test
    op.execute("ALTER TABLE question_options ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON question_options
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM questions
                JOIN tests ON tests.id = questions.test_id
                WHERE questions.id = question_options.question_id
                AND (
                    tests.school_id = current_setting('app.current_tenant_id', true)::int
                    OR tests.school_id IS NULL
                )
            )
        );
    """)

    # ===========================================
    # STEP 6: Progress tables (denormalized school_id)
    # ===========================================
    # These tables have denormalized school_id for performance (added in migration 008)

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
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")

        # Create policy: SUPER_ADMIN sees all, others see only their tenant's data
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL
            TO PUBLIC
            USING (
                current_setting('app.is_super_admin', true)::boolean = true
                OR school_id = current_setting('app.current_tenant_id', true)::int
            );
        """)

        # WITH CHECK for insert/update
        op.execute(f"""
            CREATE POLICY tenant_insert_policy ON {table}
            FOR INSERT
            TO PUBLIC
            WITH CHECK (
                current_setting('app.is_super_admin', true)::boolean = true
                OR school_id = current_setting('app.current_tenant_id', true)::int
            );
        """)

    # Test attempt answers inherit from test_attempt
    op.execute("ALTER TABLE test_attempt_answers ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON test_attempt_answers
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM test_attempts
                WHERE test_attempts.id = test_attempt_answers.attempt_id
                AND test_attempts.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)

    # ===========================================
    # STEP 7: Assignment tables
    # ===========================================

    # Assignments have school_id
    op.execute("ALTER TABLE assignments ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON assignments
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR school_id = current_setting('app.current_tenant_id', true)::int
        );
    """)
    op.execute("""
        CREATE POLICY tenant_insert_policy ON assignments
        FOR INSERT
        TO PUBLIC
        WITH CHECK (
            current_setting('app.is_super_admin', true)::boolean = true
            OR school_id = current_setting('app.current_tenant_id', true)::int
        );
    """)

    # Assignment tests inherit from assignment
    op.execute("ALTER TABLE assignment_tests ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON assignment_tests
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM assignments
                WHERE assignments.id = assignment_tests.assignment_id
                AND assignments.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)

    # Student assignments inherit from assignment
    op.execute("ALTER TABLE student_assignments ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON student_assignments
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM assignments
                WHERE assignments.id = student_assignments.assignment_id
                AND assignments.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)

    # ===========================================
    # STEP 8: Association tables (many-to-many)
    # ===========================================

    # parent_students - inherit from both parents and students
    op.execute("ALTER TABLE parent_students ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON parent_students
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM parents
                WHERE parents.id = parent_students.parent_id
                AND parents.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)

    # class_students - inherit from school_classes
    op.execute("ALTER TABLE class_students ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON class_students
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM school_classes
                WHERE school_classes.id = class_students.class_id
                AND school_classes.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)

    # class_teachers - inherit from school_classes
    op.execute("ALTER TABLE class_teachers ENABLE ROW LEVEL SECURITY;")
    op.execute("""
        CREATE POLICY tenant_isolation_policy ON class_teachers
        FOR ALL
        TO PUBLIC
        USING (
            current_setting('app.is_super_admin', true)::boolean = true
            OR EXISTS (
                SELECT 1 FROM school_classes
                WHERE school_classes.id = class_teachers.class_id
                AND school_classes.school_id = current_setting('app.current_tenant_id', true)::int
            )
        );
    """)

    # ===========================================
    # STEP 9: System tables (no RLS)
    # ===========================================
    # system_settings and analytics_events are not tenant-specific
    # No RLS applied


def downgrade() -> None:
    """
    Disable RLS and drop all policies.
    """

    # List of all tables with RLS
    all_tables = [
        # Basic tenant tables
        'schools', 'users', 'students', 'teachers', 'parents', 'school_classes',
        # Content tables (with school_id)
        'textbooks', 'tests',
        # Content hierarchy (inherit from textbook/test)
        'chapters', 'paragraphs', 'paragraph_embeddings',
        'questions', 'question_options',
        # Progress tables
        'test_attempts', 'test_attempt_answers', 'mastery_history', 'adaptive_groups',
        'student_paragraphs', 'learning_sessions', 'learning_activities', 'sync_queue',
        # Assignment tables
        'assignments', 'assignment_tests', 'student_assignments',
        # Association tables
        'parent_students', 'class_students', 'class_teachers',
    ]

    # Drop all policies and disable RLS for each table
    for table in all_tables:
        # Drop tenant_isolation_policy (if exists)
        op.execute(f"""
            DROP POLICY IF EXISTS tenant_isolation_policy ON {table};
        """)

        # Drop tenant_insert_policy (if exists)
        op.execute(f"""
            DROP POLICY IF EXISTS tenant_insert_policy ON {table};
        """)

        # Disable RLS
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # No role changes needed (we didn't grant BYPASSRLS)
