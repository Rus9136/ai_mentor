"""
Add teacher_subjects junction table for many-to-many teacher-subject relationship.

Revision ID: 073_teacher_subjects
Revises: 072_coding_chat
"""

from alembic import op
import sqlalchemy as sa  # noqa: F401

revision = "073_teacher_subjects"
down_revision = "072_coding_chat"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 1. Create junction table
    op.execute("""
        CREATE TABLE teacher_subjects (
            id SERIAL PRIMARY KEY,
            teacher_id INTEGER NOT NULL REFERENCES teachers(id) ON DELETE CASCADE,
            subject_id INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            CONSTRAINT uq_teacher_subject UNIQUE (teacher_id, subject_id)
        );

        CREATE INDEX ix_teacher_subjects_teacher_id ON teacher_subjects(teacher_id);
        CREATE INDEX ix_teacher_subjects_subject_id ON teacher_subjects(subject_id);
    """)

    # 2. Grant permissions to ai_mentor_app
    op.execute("""
        GRANT SELECT, INSERT, UPDATE, DELETE ON teacher_subjects TO ai_mentor_app;
        GRANT USAGE, SELECT ON SEQUENCE teacher_subjects_id_seq TO ai_mentor_app;
    """)

    # 3. Migrate existing data: copy current subject_id into junction table
    op.execute("""
        INSERT INTO teacher_subjects (teacher_id, subject_id)
        SELECT id, subject_id
        FROM teachers
        WHERE subject_id IS NOT NULL AND is_deleted = false;
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS teacher_subjects CASCADE;")
