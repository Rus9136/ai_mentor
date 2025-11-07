-- Fix RLS policies to handle NULL session variables properly
-- This script recreates all policies with COALESCE to prevent cast errors

-- ===========================================
-- STEP 1: Schools table
-- ===========================================
DROP POLICY IF EXISTS tenant_isolation_policy ON schools;
CREATE POLICY tenant_isolation_policy ON schools
FOR ALL
TO PUBLIC
USING (
    COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
    OR id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
);

-- ===========================================
-- STEP 2: Basic tenant tables
-- ===========================================
DO $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT unnest(ARRAY['users', 'students', 'teachers', 'parents', 'school_classes'])
    LOOP
        -- Drop existing policies
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I', table_name);
        EXECUTE format('DROP POLICY IF EXISTS tenant_insert_policy ON %I', table_name);

        -- Create tenant_isolation_policy
        EXECUTE format($fmt$
            CREATE POLICY tenant_isolation_policy ON %I
            FOR ALL
            TO PUBLIC
            USING (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        $fmt$, table_name);

        -- Create tenant_insert_policy
        EXECUTE format($fmt$
            CREATE POLICY tenant_insert_policy ON %I
            FOR INSERT
            TO PUBLIC
            WITH CHECK (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        $fmt$, table_name);

        RAISE NOTICE 'Updated policies for table: %', table_name;
    END LOOP;
END $$;

-- ===========================================
-- STEP 3: Content tables (textbooks, tests) - with global support
-- ===========================================
DO $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT unnest(ARRAY['textbooks', 'tests'])
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I', table_name);
        EXECUTE format('DROP POLICY IF EXISTS tenant_insert_policy ON %I', table_name);

        EXECUTE format($fmt$
            CREATE POLICY tenant_isolation_policy ON %I
            FOR ALL
            TO PUBLIC
            USING (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                OR school_id IS NULL  -- Global content
            )
        $fmt$, table_name);

        EXECUTE format($fmt$
            CREATE POLICY tenant_insert_policy ON %I
            FOR INSERT
            TO PUBLIC
            WITH CHECK (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                OR school_id IS NULL
            )
        $fmt$, table_name);

        RAISE NOTICE 'Updated policies for table: %', table_name;
    END LOOP;
END $$;

-- ===========================================
-- STEP 4: Content hierarchy (inherit from textbooks)
-- ===========================================

-- Chapters
DROP POLICY IF EXISTS tenant_isolation_policy ON chapters;
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

-- Paragraphs
DROP POLICY IF EXISTS tenant_isolation_policy ON paragraphs;
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

-- Paragraph embeddings
DROP POLICY IF EXISTS tenant_isolation_policy ON paragraph_embeddings;
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

-- ===========================================
-- STEP 5: Questions hierarchy (inherit from tests)
-- ===========================================

-- Questions
DROP POLICY IF EXISTS tenant_isolation_policy ON questions;
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

-- Question options
DROP POLICY IF EXISTS tenant_isolation_policy ON question_options;
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

-- ===========================================
-- STEP 6: Progress tables
-- ===========================================
DO $$
DECLARE
    table_name text;
BEGIN
    FOR table_name IN
        SELECT unnest(ARRAY[
            'test_attempts', 'mastery_history', 'adaptive_groups',
            'student_paragraphs', 'learning_sessions', 'learning_activities', 'sync_queue'
        ])
    LOOP
        EXECUTE format('DROP POLICY IF EXISTS tenant_isolation_policy ON %I', table_name);
        EXECUTE format('DROP POLICY IF EXISTS tenant_insert_policy ON %I', table_name);

        EXECUTE format($fmt$
            CREATE POLICY tenant_isolation_policy ON %I
            FOR ALL
            TO PUBLIC
            USING (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        $fmt$, table_name);

        EXECUTE format($fmt$
            CREATE POLICY tenant_insert_policy ON %I
            FOR INSERT
            TO PUBLIC
            WITH CHECK (
                COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
                OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        $fmt$, table_name);

        RAISE NOTICE 'Updated policies for table: %', table_name;
    END LOOP;
END $$;

-- Test attempt answers (inherit from test_attempts)
DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempt_answers;
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

-- ===========================================
-- STEP 7: Assignment tables
-- ===========================================

-- Assignments
DROP POLICY IF EXISTS tenant_isolation_policy ON assignments;
DROP POLICY IF EXISTS tenant_insert_policy ON assignments;
CREATE POLICY tenant_isolation_policy ON assignments
FOR ALL
TO PUBLIC
USING (
    COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
    OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
);
CREATE POLICY tenant_insert_policy ON assignments
FOR INSERT
TO PUBLIC
WITH CHECK (
    COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
    OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
);

-- Assignment tests (inherit from assignments)
DROP POLICY IF EXISTS tenant_isolation_policy ON assignment_tests;
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

-- Student assignments (inherit from assignments)
DROP POLICY IF EXISTS tenant_isolation_policy ON student_assignments;
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

-- ===========================================
-- STEP 8: Association tables
-- ===========================================

-- parent_students
DROP POLICY IF EXISTS tenant_isolation_policy ON parent_students;
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

-- class_students
DROP POLICY IF EXISTS tenant_isolation_policy ON class_students;
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

-- class_teachers
DROP POLICY IF EXISTS tenant_isolation_policy ON class_teachers;
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
