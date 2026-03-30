"""
Add subject_id and is_homeroom to class_teachers table.

Allows assigning teachers to classes per-subject and designating
one homeroom teacher (классный руководитель) per class.

Revision ID: 075_class_teacher_subject_homeroom
Revises: 074_quiz_factile
"""

revision = '075_class_teacher_subject_homeroom'
down_revision = '074_quiz_factile'

from alembic import op
import sqlalchemy as sa


def upgrade():
    # 1. Add subject_id column (nullable FK to subjects)
    op.add_column('class_teachers', sa.Column(
        'subject_id', sa.Integer,
        sa.ForeignKey('subjects.id', ondelete='SET NULL'),
        nullable=True
    ))
    op.create_index('ix_class_teachers_subject_id', 'class_teachers', ['subject_id'])

    # 2. Add is_homeroom column
    op.add_column('class_teachers', sa.Column(
        'is_homeroom', sa.Boolean, nullable=False, server_default='false'
    ))

    # 3. Replace unique constraint: (class_id, teacher_id) -> (class_id, teacher_id, subject_id)
    op.drop_constraint('uq_class_teacher', 'class_teachers', type_='unique')
    op.create_unique_constraint(
        'uq_class_teacher_subject', 'class_teachers',
        ['class_id', 'teacher_id', 'subject_id']
    )

    # 4. Partial unique index for NULL subject_id duplicates
    #    (PostgreSQL treats NULLs as distinct in unique constraints)
    op.execute("""
        CREATE UNIQUE INDEX uq_class_teacher_null_subject
        ON class_teachers (class_id, teacher_id)
        WHERE subject_id IS NULL
    """)

    # 5. Partial unique index: at most one homeroom teacher per class
    op.execute("""
        CREATE UNIQUE INDEX uq_class_homeroom
        ON class_teachers (class_id)
        WHERE is_homeroom = true
    """)


def downgrade():
    op.execute("DROP INDEX IF EXISTS uq_class_homeroom")
    op.execute("DROP INDEX IF EXISTS uq_class_teacher_null_subject")
    op.drop_constraint('uq_class_teacher_subject', 'class_teachers', type_='unique')
    op.create_unique_constraint('uq_class_teacher', 'class_teachers', ['class_id', 'teacher_id'])
    op.drop_index('ix_class_teachers_subject_id', 'class_teachers')
    op.drop_column('class_teachers', 'is_homeroom')
    op.drop_column('class_teachers', 'subject_id')
