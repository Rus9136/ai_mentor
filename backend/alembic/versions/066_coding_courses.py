"""
Add coding courses (learning paths) tables.

Tables:
- coding_courses: Course metadata (title, slug, grade, etc.)
- coding_lessons: Lessons within courses (theory + optional challenge)
- coding_course_progress: Student progress per course

Revision ID: 066_coding_courses
Revises: 065_coding_challenges
"""
revision = "066_coding_courses"
down_revision = "065_coding_challenges"

from alembic import op


def upgrade() -> None:
    # ------------------------------------------------------------------
    # coding_courses
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE coding_courses (
            id SERIAL PRIMARY KEY,
            title VARCHAR(300) NOT NULL,
            title_kk VARCHAR(300),
            description TEXT,
            description_kk TEXT,
            slug VARCHAR(50) UNIQUE NOT NULL,
            grade_level INTEGER,
            total_lessons INTEGER NOT NULL DEFAULT 0,
            estimated_hours FLOAT,
            sort_order INTEGER NOT NULL DEFAULT 0,
            icon VARCHAR(50),
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX idx_coding_courses_slug ON coding_courses(slug);
        CREATE INDEX idx_coding_courses_sort ON coding_courses(sort_order);
    """)

    # ------------------------------------------------------------------
    # coding_lessons
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE coding_lessons (
            id SERIAL PRIMARY KEY,
            course_id INTEGER NOT NULL REFERENCES coding_courses(id) ON DELETE CASCADE,
            title VARCHAR(300) NOT NULL,
            title_kk VARCHAR(300),
            sort_order INTEGER NOT NULL DEFAULT 0,
            theory_content TEXT NOT NULL,
            theory_content_kk TEXT,
            starter_code TEXT,
            challenge_id INTEGER REFERENCES coding_challenges(id) ON DELETE SET NULL,
            is_active BOOLEAN NOT NULL DEFAULT TRUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );

        CREATE INDEX idx_coding_lessons_course_sort ON coding_lessons(course_id, sort_order);
    """)

    # ------------------------------------------------------------------
    # coding_course_progress
    # ------------------------------------------------------------------
    op.execute("""
        CREATE TABLE coding_course_progress (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            course_id INTEGER NOT NULL REFERENCES coding_courses(id) ON DELETE CASCADE,
            last_lesson_id INTEGER REFERENCES coding_lessons(id) ON DELETE SET NULL,
            completed_lessons INTEGER NOT NULL DEFAULT 0,
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            UNIQUE(student_id, course_id)
        );

        CREATE INDEX idx_coding_course_progress_student ON coding_course_progress(student_id);
        CREATE INDEX idx_coding_course_progress_course ON coding_course_progress(course_id);
    """)

    # ------------------------------------------------------------------
    # Grants for runtime user
    # ------------------------------------------------------------------
    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON coding_courses TO ai_mentor_app;
        GRANT USAGE, SELECT ON SEQUENCE coding_courses_id_seq TO ai_mentor_app;

        GRANT SELECT, INSERT, UPDATE, DELETE ON coding_lessons TO ai_mentor_app;
        GRANT USAGE, SELECT ON SEQUENCE coding_lessons_id_seq TO ai_mentor_app;

        GRANT SELECT, INSERT, UPDATE, DELETE ON coding_course_progress TO ai_mentor_app;
        GRANT USAGE, SELECT ON SEQUENCE coding_course_progress_id_seq TO ai_mentor_app;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS coding_course_progress CASCADE;")
    op.execute("DROP TABLE IF EXISTS coding_lessons CASCADE;")
    op.execute("DROP TABLE IF EXISTS coding_courses CASCADE;")
