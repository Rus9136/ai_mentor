-- Migration 008: Add school_id to progress tables for data isolation
-- This migration adds school_id to all progress tracking tables for better
-- data isolation, performance, and scalability.

-- ============================================================================
-- STEP 1: Add school_id columns (nullable first)
-- ============================================================================

ALTER TABLE test_attempts ADD COLUMN school_id INT;
ALTER TABLE mastery_history ADD COLUMN school_id INT;
ALTER TABLE adaptive_groups ADD COLUMN school_id INT;
ALTER TABLE student_paragraphs ADD COLUMN school_id INT;
ALTER TABLE learning_sessions ADD COLUMN school_id INT;
ALTER TABLE learning_activities ADD COLUMN school_id INT;
ALTER TABLE analytics_events ADD COLUMN school_id INT;
ALTER TABLE sync_queue ADD COLUMN school_id INT;


-- ============================================================================
-- STEP 2: Fill school_id from students table
-- ============================================================================

UPDATE test_attempts
SET school_id = (SELECT school_id FROM students WHERE students.id = test_attempts.student_id)
WHERE student_id IS NOT NULL;

UPDATE mastery_history
SET school_id = (SELECT school_id FROM students WHERE students.id = mastery_history.student_id)
WHERE student_id IS NOT NULL;

UPDATE adaptive_groups
SET school_id = (SELECT school_id FROM students WHERE students.id = adaptive_groups.student_id)
WHERE student_id IS NOT NULL;

UPDATE student_paragraphs
SET school_id = (SELECT school_id FROM students WHERE students.id = student_paragraphs.student_id)
WHERE student_id IS NOT NULL;

UPDATE learning_sessions
SET school_id = (SELECT school_id FROM students WHERE students.id = learning_sessions.student_id)
WHERE student_id IS NOT NULL;

UPDATE learning_activities
SET school_id = (SELECT school_id FROM students WHERE students.id = learning_activities.student_id)
WHERE student_id IS NOT NULL;

UPDATE analytics_events
SET school_id = (SELECT school_id FROM students WHERE students.id = analytics_events.student_id)
WHERE student_id IS NOT NULL;

UPDATE sync_queue
SET school_id = (SELECT school_id FROM students WHERE students.id = sync_queue.student_id)
WHERE student_id IS NOT NULL;


-- ============================================================================
-- STEP 3: Make school_id NOT NULL (except analytics_events)
-- ============================================================================

ALTER TABLE test_attempts ALTER COLUMN school_id SET NOT NULL;
ALTER TABLE mastery_history ALTER COLUMN school_id SET NOT NULL;
ALTER TABLE adaptive_groups ALTER COLUMN school_id SET NOT NULL;
ALTER TABLE student_paragraphs ALTER COLUMN school_id SET NOT NULL;
ALTER TABLE learning_sessions ALTER COLUMN school_id SET NOT NULL;
ALTER TABLE learning_activities ALTER COLUMN school_id SET NOT NULL;
-- analytics_events.school_id stays nullable (some events may not be tied to a student)
ALTER TABLE sync_queue ALTER COLUMN school_id SET NOT NULL;


-- ============================================================================
-- STEP 4: Add foreign key constraints
-- ============================================================================

ALTER TABLE test_attempts ADD CONSTRAINT fk_test_attempts_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE mastery_history ADD CONSTRAINT fk_mastery_history_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE adaptive_groups ADD CONSTRAINT fk_adaptive_groups_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE student_paragraphs ADD CONSTRAINT fk_student_paragraphs_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE learning_sessions ADD CONSTRAINT fk_learning_sessions_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE learning_activities ADD CONSTRAINT fk_learning_activities_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE analytics_events ADD CONSTRAINT fk_analytics_events_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

ALTER TABLE sync_queue ADD CONSTRAINT fk_sync_queue_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;


-- ============================================================================
-- STEP 5: Create single column indexes
-- ============================================================================

CREATE INDEX ix_test_attempts_school_id ON test_attempts(school_id);
CREATE INDEX ix_mastery_history_school_id ON mastery_history(school_id);
CREATE INDEX ix_adaptive_groups_school_id ON adaptive_groups(school_id);
CREATE INDEX ix_student_paragraphs_school_id ON student_paragraphs(school_id);
CREATE INDEX ix_learning_sessions_school_id ON learning_sessions(school_id);
CREATE INDEX ix_learning_activities_school_id ON learning_activities(school_id);
CREATE INDEX ix_analytics_events_school_id ON analytics_events(school_id);
CREATE INDEX ix_sync_queue_school_id ON sync_queue(school_id);


-- ============================================================================
-- STEP 6: Create composite indexes for common queries
-- ============================================================================

-- test_attempts: queries like "get all attempts for school X and student Y"
CREATE INDEX ix_test_attempts_school_student ON test_attempts(school_id, student_id);
CREATE INDEX ix_test_attempts_school_created ON test_attempts(school_id, created_at);

-- mastery_history: queries like "get mastery for school X and paragraph Y"
CREATE INDEX ix_mastery_history_school_student ON mastery_history(school_id, student_id);
CREATE INDEX ix_mastery_history_school_paragraph ON mastery_history(school_id, paragraph_id);

-- adaptive_groups: queries like "get group for school X and student Y"
CREATE INDEX ix_adaptive_groups_school_student ON adaptive_groups(school_id, student_id);

-- student_paragraphs: queries like "get progress for school X and student Y"
CREATE INDEX ix_student_paragraphs_school_student ON student_paragraphs(school_id, student_id);

-- learning_sessions: queries like "get sessions for school X in date range"
CREATE INDEX ix_learning_sessions_school_start ON learning_sessions(school_id, session_start);

-- learning_activities: queries like "get activities for school X by type/date"
CREATE INDEX ix_learning_activities_school_timestamp ON learning_activities(school_id, activity_timestamp);
CREATE INDEX ix_learning_activities_school_type ON learning_activities(school_id, activity_type);

-- analytics_events: queries like "get events for school X in date range"
CREATE INDEX ix_analytics_events_school_timestamp ON analytics_events(school_id, event_timestamp);

-- sync_queue: queries like "get pending sync items for school X"
CREATE INDEX ix_sync_queue_school_status ON sync_queue(school_id, status);


-- ============================================================================
-- STEP 7: Add CHECK constraints for data consistency
-- ============================================================================

ALTER TABLE test_attempts ADD CONSTRAINT check_test_attempts_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE mastery_history ADD CONSTRAINT check_mastery_history_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE adaptive_groups ADD CONSTRAINT check_adaptive_groups_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE student_paragraphs ADD CONSTRAINT check_student_paragraphs_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE learning_sessions ADD CONSTRAINT check_learning_sessions_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE learning_activities ADD CONSTRAINT check_learning_activities_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE analytics_events ADD CONSTRAINT check_analytics_events_school
    CHECK (student_id IS NULL OR school_id = (SELECT school_id FROM students WHERE id = student_id));

ALTER TABLE sync_queue ADD CONSTRAINT check_sync_queue_school
    CHECK (school_id = (SELECT school_id FROM students WHERE id = student_id));


-- ============================================================================
-- STEP 8: Hybrid model for textbooks (make school_id nullable)
-- ============================================================================

ALTER TABLE textbooks ALTER COLUMN school_id DROP NOT NULL;

-- Add hybrid model fields
ALTER TABLE textbooks ADD COLUMN global_textbook_id INT;
ALTER TABLE textbooks ADD COLUMN is_customized BOOLEAN NOT NULL DEFAULT false;

-- Add foreign key and indexes
ALTER TABLE textbooks ADD CONSTRAINT fk_textbooks_global
    FOREIGN KEY (global_textbook_id) REFERENCES textbooks(id) ON DELETE SET NULL;

CREATE INDEX ix_textbooks_global_textbook_id ON textbooks(global_textbook_id);
CREATE INDEX ix_textbooks_school_global ON textbooks(school_id, global_textbook_id);

COMMENT ON COLUMN textbooks.school_id IS 'NULL = global textbook, NOT NULL = school-specific textbook';
COMMENT ON COLUMN textbooks.global_textbook_id IS 'Reference to global textbook if this is a customized version';
COMMENT ON COLUMN textbooks.is_customized IS 'true if school has modified the content from global version';


-- ============================================================================
-- STEP 9: Add school_id to tests (nullable for global tests)
-- ============================================================================

ALTER TABLE tests ADD COLUMN school_id INT;

ALTER TABLE tests ADD CONSTRAINT fk_tests_school
    FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

CREATE INDEX ix_tests_school_id ON tests(school_id);

COMMENT ON COLUMN tests.school_id IS 'NULL = global test, NOT NULL = school-specific test';


-- ============================================================================
-- STEP 10: Update alembic version
-- ============================================================================

UPDATE alembic_version SET version_num = '008';


-- ============================================================================
-- Migration completed successfully!
-- ============================================================================

-- Summary:
-- - Added school_id to 8 progress tracking tables
-- - Created 8 single-column indexes and 11 composite indexes
-- - Added 8 CHECK constraints for data consistency
-- - Made textbooks.school_id nullable for hybrid model
-- - Added hybrid model fields (global_textbook_id, is_customized)
-- - Added school_id to tests table
-- - All changes enable better isolation, performance, and scalability
