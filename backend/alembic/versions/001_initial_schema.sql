-- Initial schema migration
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create enums
CREATE TYPE userrole AS ENUM ('admin', 'teacher', 'student', 'parent');
CREATE TYPE difficultylevel AS ENUM ('easy', 'medium', 'hard');
CREATE TYPE questiontype AS ENUM ('single_choice', 'multiple_choice', 'true_false', 'short_answer');
CREATE TYPE attemptstatus AS ENUM ('in_progress', 'completed', 'abandoned');
CREATE TYPE assignmentstatus AS ENUM ('not_started', 'in_progress', 'completed', 'overdue');
CREATE TYPE activitytype AS ENUM ('read_paragraph', 'watch_video', 'complete_test', 'ask_question', 'view_explanation');
CREATE TYPE syncstatus AS ENUM ('pending', 'syncing', 'completed', 'failed');

-- Create schools table
CREATE TABLE schools (
    id SERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    code VARCHAR(50) NOT NULL UNIQUE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    email VARCHAR(255),
    phone VARCHAR(50),
    address TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_schools_name ON schools(name);
CREATE INDEX ix_schools_code ON schools(code);

-- Create users table
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT true,
    is_verified BOOLEAN NOT NULL DEFAULT false,
    first_name VARCHAR(100) NOT NULL,
    last_name VARCHAR(100) NOT NULL,
    middle_name VARCHAR(100),
    phone VARCHAR(50),
    role userrole NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_users_school_id ON users(school_id);
CREATE INDEX ix_users_email ON users(email);
CREATE INDEX ix_users_role ON users(role);

-- Create students table
CREATE TABLE students (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    student_code VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    birth_date DATE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_students_school_id ON students(school_id);
CREATE INDEX ix_students_user_id ON students(user_id);
CREATE INDEX ix_students_student_code ON students(student_code);
CREATE INDEX ix_students_grade_level ON students(grade_level);

-- Create teachers table
CREATE TABLE teachers (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    user_id INTEGER NOT NULL UNIQUE REFERENCES users(id) ON DELETE CASCADE,
    teacher_code VARCHAR(50) NOT NULL,
    subject VARCHAR(100),
    bio TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_teachers_school_id ON teachers(school_id);
CREATE INDEX ix_teachers_user_id ON teachers(user_id);
CREATE INDEX ix_teachers_teacher_code ON teachers(teacher_code);

-- Create school_classes table
CREATE TABLE school_classes (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    name VARCHAR(100) NOT NULL,
    code VARCHAR(50) NOT NULL,
    grade_level INTEGER NOT NULL,
    academic_year VARCHAR(20) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false,
    CONSTRAINT uq_school_class_code UNIQUE (school_id, code)
);

CREATE INDEX ix_school_classes_school_id ON school_classes(school_id);
CREATE INDEX ix_school_classes_code ON school_classes(code);
CREATE INDEX ix_school_classes_grade_level ON school_classes(grade_level);
CREATE INDEX ix_school_classes_academic_year ON school_classes(academic_year);

-- Create class_students association table
CREATE TABLE class_students (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES school_classes(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    CONSTRAINT uq_class_student UNIQUE (class_id, student_id)
);

-- Create class_teachers association table
CREATE TABLE class_teachers (
    id SERIAL PRIMARY KEY,
    class_id INTEGER NOT NULL REFERENCES school_classes(id) ON DELETE CASCADE,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    CONSTRAINT uq_class_teacher UNIQUE (class_id, teacher_id)
);

-- Create textbooks table
CREATE TABLE textbooks (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    subject VARCHAR(100) NOT NULL,
    grade_level INTEGER NOT NULL,
    author VARCHAR(255),
    publisher VARCHAR(255),
    year INTEGER,
    isbn VARCHAR(50),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_textbooks_school_id ON textbooks(school_id);
CREATE INDEX ix_textbooks_title ON textbooks(title);
CREATE INDEX ix_textbooks_subject ON textbooks(subject);
CREATE INDEX ix_textbooks_grade_level ON textbooks(grade_level);

-- Create chapters table
CREATE TABLE chapters (
    id SERIAL PRIMARY KEY,
    textbook_id INTEGER NOT NULL REFERENCES textbooks(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    number INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_chapters_textbook_id ON chapters(textbook_id);

-- Create paragraphs table
CREATE TABLE paragraphs (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER NOT NULL REFERENCES chapters(id) ON DELETE CASCADE,
    title VARCHAR(255),
    number INTEGER NOT NULL,
    "order" INTEGER NOT NULL,
    content TEXT NOT NULL,
    summary TEXT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_paragraphs_chapter_id ON paragraphs(chapter_id);

-- Create paragraph_embeddings table
CREATE TABLE paragraph_embeddings (
    id SERIAL PRIMARY KEY,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text TEXT NOT NULL,
    embedding vector(1536) NOT NULL,
    model VARCHAR(100) NOT NULL DEFAULT 'text-embedding-3-small',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_paragraph_embeddings_paragraph_id ON paragraph_embeddings(paragraph_id);

-- Create tests table
CREATE TABLE tests (
    id SERIAL PRIMARY KEY,
    chapter_id INTEGER REFERENCES chapters(id) ON DELETE CASCADE,
    paragraph_id INTEGER REFERENCES paragraphs(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    difficulty difficultylevel NOT NULL DEFAULT 'medium',
    time_limit INTEGER,
    passing_score FLOAT NOT NULL DEFAULT 0.7,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_tests_chapter_id ON tests(chapter_id);
CREATE INDEX ix_tests_paragraph_id ON tests(paragraph_id);

-- Create questions table
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    "order" INTEGER NOT NULL,
    question_type questiontype NOT NULL,
    question_text TEXT NOT NULL,
    explanation TEXT,
    points FLOAT NOT NULL DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_questions_test_id ON questions(test_id);

-- Create question_options table
CREATE TABLE question_options (
    id SERIAL PRIMARY KEY,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    "order" INTEGER NOT NULL,
    option_text TEXT NOT NULL,
    is_correct BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_question_options_question_id ON question_options(question_id);

-- Create test_attempts table
CREATE TABLE test_attempts (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    attempt_number INTEGER NOT NULL DEFAULT 1,
    status attemptstatus NOT NULL DEFAULT 'in_progress',
    started_at TIMESTAMP WITH TIME ZONE NOT NULL,
    completed_at TIMESTAMP WITH TIME ZONE,
    score FLOAT,
    points_earned FLOAT,
    total_points FLOAT,
    passed BOOLEAN,
    time_spent INTEGER,
    synced_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_test_attempts_student_id ON test_attempts(student_id);
CREATE INDEX ix_test_attempts_test_id ON test_attempts(test_id);
CREATE INDEX ix_test_attempts_status ON test_attempts(status);

-- Create test_attempt_answers table
CREATE TABLE test_attempt_answers (
    id SERIAL PRIMARY KEY,
    attempt_id INTEGER NOT NULL REFERENCES test_attempts(id) ON DELETE CASCADE,
    question_id INTEGER NOT NULL REFERENCES questions(id) ON DELETE CASCADE,
    selected_option_ids TEXT,
    answer_text TEXT,
    is_correct BOOLEAN,
    points_earned FLOAT,
    answered_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_test_attempt_answers_attempt_id ON test_attempt_answers(attempt_id);
CREATE INDEX ix_test_attempt_answers_question_id ON test_attempt_answers(question_id);

-- Create mastery_history table
CREATE TABLE mastery_history (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    mastery_score FLOAT NOT NULL,
    attempts_count INTEGER NOT NULL DEFAULT 0,
    success_rate FLOAT NOT NULL DEFAULT 0.0,
    recorded_at TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_mastery_history_student_id ON mastery_history(student_id);
CREATE INDEX ix_mastery_history_paragraph_id ON mastery_history(paragraph_id);
CREATE INDEX ix_mastery_history_recorded_at ON mastery_history(recorded_at);

-- Create adaptive_groups table
CREATE TABLE adaptive_groups (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    group_name VARCHAR(10) NOT NULL,
    assigned_at TIMESTAMP WITH TIME ZONE NOT NULL,
    mastery_score FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_adaptive_groups_student_id ON adaptive_groups(student_id);
CREATE INDEX ix_adaptive_groups_paragraph_id ON adaptive_groups(paragraph_id);
CREATE INDEX ix_adaptive_groups_group_name ON adaptive_groups(group_name);

-- Create assignments table
CREATE TABLE assignments (
    id SERIAL PRIMARY KEY,
    school_id INTEGER NOT NULL REFERENCES schools(id) ON DELETE CASCADE,
    class_id INTEGER NOT NULL REFERENCES school_classes(id) ON DELETE CASCADE,
    teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    due_date TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN NOT NULL DEFAULT true,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_assignments_school_id ON assignments(school_id);
CREATE INDEX ix_assignments_class_id ON assignments(class_id);
CREATE INDEX ix_assignments_teacher_id ON assignments(teacher_id);
CREATE INDEX ix_assignments_due_date ON assignments(due_date);

-- Create assignment_tests association table
CREATE TABLE assignment_tests (
    id SERIAL PRIMARY KEY,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    test_id INTEGER NOT NULL REFERENCES tests(id) ON DELETE CASCADE,
    "order" INTEGER NOT NULL DEFAULT 0
);

-- Create student_assignments table
CREATE TABLE student_assignments (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    assignment_id INTEGER NOT NULL REFERENCES assignments(id) ON DELETE CASCADE,
    status assignmentstatus NOT NULL DEFAULT 'not_started',
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    progress_percentage INTEGER NOT NULL DEFAULT 0,
    score FLOAT,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    deleted_at TIMESTAMP WITH TIME ZONE,
    is_deleted BOOLEAN NOT NULL DEFAULT false
);

CREATE INDEX ix_student_assignments_student_id ON student_assignments(student_id);
CREATE INDEX ix_student_assignments_assignment_id ON student_assignments(assignment_id);
CREATE INDEX ix_student_assignments_status ON student_assignments(status);

-- Create student_paragraphs table
CREATE TABLE student_paragraphs (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    paragraph_id INTEGER NOT NULL REFERENCES paragraphs(id) ON DELETE CASCADE,
    is_completed BOOLEAN NOT NULL DEFAULT false,
    time_spent INTEGER NOT NULL DEFAULT 0,
    last_accessed_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_student_paragraphs_student_id ON student_paragraphs(student_id);
CREATE INDEX ix_student_paragraphs_paragraph_id ON student_paragraphs(paragraph_id);

-- Create learning_sessions table
CREATE TABLE learning_sessions (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    session_start TIMESTAMP WITH TIME ZONE NOT NULL,
    session_end TIMESTAMP WITH TIME ZONE,
    duration INTEGER,
    device_id VARCHAR(255),
    device_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_learning_sessions_student_id ON learning_sessions(student_id);
CREATE INDEX ix_learning_sessions_session_start ON learning_sessions(session_start);

-- Create learning_activities table
CREATE TABLE learning_activities (
    id SERIAL PRIMARY KEY,
    session_id INTEGER NOT NULL REFERENCES learning_sessions(id) ON DELETE CASCADE,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    activity_type activitytype NOT NULL,
    activity_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    duration INTEGER,
    paragraph_id INTEGER REFERENCES paragraphs(id) ON DELETE SET NULL,
    test_id INTEGER REFERENCES tests(id) ON DELETE SET NULL,
    metadata JSON,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_learning_activities_session_id ON learning_activities(session_id);
CREATE INDEX ix_learning_activities_activity_type ON learning_activities(activity_type);
CREATE INDEX ix_learning_activities_activity_timestamp ON learning_activities(activity_timestamp);

-- Create analytics_events table
CREATE TABLE analytics_events (
    id SERIAL PRIMARY KEY,
    student_id INTEGER REFERENCES students(id) ON DELETE CASCADE,
    event_type VARCHAR(100) NOT NULL,
    event_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    event_data JSON,
    user_agent VARCHAR(500),
    ip_address VARCHAR(50),
    device_type VARCHAR(50),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_analytics_events_student_id ON analytics_events(student_id);
CREATE INDEX ix_analytics_events_event_type ON analytics_events(event_type);
CREATE INDEX ix_analytics_events_event_timestamp ON analytics_events(event_timestamp);

-- Create sync_queue table
CREATE TABLE sync_queue (
    id SERIAL PRIMARY KEY,
    student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
    entity_type VARCHAR(100) NOT NULL,
    entity_id INTEGER,
    operation VARCHAR(20) NOT NULL,
    data TEXT NOT NULL,
    status syncstatus NOT NULL DEFAULT 'pending',
    attempts INTEGER NOT NULL DEFAULT 0,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    error_message TEXT,
    device_id VARCHAR(255),
    created_at_device TIMESTAMP WITH TIME ZONE NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_sync_queue_student_id ON sync_queue(student_id);
CREATE INDEX ix_sync_queue_entity_type ON sync_queue(entity_type);
CREATE INDEX ix_sync_queue_status ON sync_queue(status);

-- Create system_settings table
CREATE TABLE system_settings (
    id SERIAL PRIMARY KEY,
    key VARCHAR(255) NOT NULL UNIQUE,
    value TEXT,
    description TEXT,
    is_public BOOLEAN NOT NULL DEFAULT false,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_system_settings_key ON system_settings(key);

-- Create alembic_version table for migration tracking
CREATE TABLE alembic_version (
    version_num VARCHAR(32) NOT NULL,
    CONSTRAINT alembic_version_pkc PRIMARY KEY (version_num)
);

INSERT INTO alembic_version (version_num) VALUES ('001');
