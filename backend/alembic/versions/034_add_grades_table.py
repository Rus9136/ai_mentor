"""Add grades table for school gradebook (journal)

Revision ID: 034_grades
Revises: 033_app_versions
Create Date: 2026-02-28
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '034_grades'
down_revision = '033_app_versions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create grade_type enum
    grade_type_enum = sa.Enum('CURRENT', 'SOR', 'SOCH', 'EXAM', name='grade_type')
    grade_type_enum.create(op.get_bind(), checkfirst=True)

    # Create grades table
    op.create_table(
        'grades',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('subject_id', sa.Integer(), sa.ForeignKey('subjects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.Integer(), sa.ForeignKey('school_classes.id', ondelete='SET NULL'), nullable=True),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('grade_value', sa.SmallInteger(), nullable=False),
        sa.Column('grade_type', grade_type_enum, nullable=False, server_default='CURRENT'),
        sa.Column('grade_date', sa.Date(), nullable=False),
        sa.Column('quarter', sa.SmallInteger(), nullable=False),
        sa.Column('academic_year', sa.String(9), nullable=False),
        sa.Column('comment', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('grade_value BETWEEN 1 AND 10', name='ck_grades_grade_value'),
        sa.CheckConstraint('quarter BETWEEN 1 AND 4', name='ck_grades_quarter'),
    )

    # Indexes (partial — only non-deleted)
    op.execute(
        "CREATE INDEX ix_grades_student_subject_quarter "
        "ON grades(school_id, student_id, subject_id, quarter) "
        "WHERE is_deleted = FALSE"
    )
    op.execute(
        "CREATE INDEX ix_grades_class_subject_date "
        "ON grades(school_id, class_id, subject_id, grade_date) "
        "WHERE is_deleted = FALSE"
    )
    op.execute(
        "CREATE INDEX ix_grades_student_year "
        "ON grades(school_id, student_id, academic_year) "
        "WHERE is_deleted = FALSE"
    )
    op.execute(
        "CREATE INDEX ix_grades_teacher "
        "ON grades(teacher_id) "
        "WHERE is_deleted = FALSE"
    )

    # Grant permissions to app user
    op.execute("GRANT SELECT, INSERT, UPDATE ON grades TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE grades_id_seq TO ai_mentor_app")


def downgrade() -> None:
    op.drop_table('grades')
    sa.Enum(name='grade_type').drop(op.get_bind(), checkfirst=True)
