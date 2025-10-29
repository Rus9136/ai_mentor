"""Add indexes for soft delete filtering

Revision ID: 006
Revises: 005
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006'
down_revision: Union[str, None] = '005'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite indexes on (is_deleted, created_at) for all soft delete tables
    # This optimizes queries that filter by is_deleted and order by created_at

    # Core/Organizational tables
    op.create_index(
        'ix_schools_is_deleted_created',
        'schools',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_users_is_deleted_created',
        'users',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_students_is_deleted_created',
        'students',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_teachers_is_deleted_created',
        'teachers',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_school_classes_is_deleted_created',
        'school_classes',
        ['is_deleted', 'created_at'],
        unique=False
    )

    # Content tables
    op.create_index(
        'ix_textbooks_is_deleted_created',
        'textbooks',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_chapters_is_deleted_created',
        'chapters',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_paragraphs_is_deleted_created',
        'paragraphs',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_paragraph_embeddings_is_deleted_created',
        'paragraph_embeddings',
        ['is_deleted', 'created_at'],
        unique=False
    )

    # Test tables
    op.create_index(
        'ix_tests_is_deleted_created',
        'tests',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_questions_is_deleted_created',
        'questions',
        ['is_deleted', 'created_at'],
        unique=False
    )

    op.create_index(
        'ix_question_options_is_deleted_created',
        'question_options',
        ['is_deleted', 'created_at'],
        unique=False
    )

    # Assignment tables
    op.create_index(
        'ix_assignments_is_deleted_created',
        'assignments',
        ['is_deleted', 'created_at'],
        unique=False
    )

    # NOTE: assignment_tests does NOT have soft delete fields in DB (migration 001 error)
    # Skipped until migration 007 fixes this

    op.create_index(
        'ix_student_assignments_is_deleted_created',
        'student_assignments',
        ['is_deleted', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    # Remove soft delete indexes
    op.drop_index('ix_student_assignments_is_deleted_created', table_name='student_assignments')
    # NOTE: assignment_tests index was not created (see upgrade notes)
    op.drop_index('ix_assignments_is_deleted_created', table_name='assignments')
    op.drop_index('ix_question_options_is_deleted_created', table_name='question_options')
    op.drop_index('ix_questions_is_deleted_created', table_name='questions')
    op.drop_index('ix_tests_is_deleted_created', table_name='tests')
    op.drop_index('ix_paragraph_embeddings_is_deleted_created', table_name='paragraph_embeddings')
    op.drop_index('ix_paragraphs_is_deleted_created', table_name='paragraphs')
    op.drop_index('ix_chapters_is_deleted_created', table_name='chapters')
    op.drop_index('ix_textbooks_is_deleted_created', table_name='textbooks')
    op.drop_index('ix_school_classes_is_deleted_created', table_name='school_classes')
    op.drop_index('ix_teachers_is_deleted_created', table_name='teachers')
    op.drop_index('ix_students_is_deleted_created', table_name='students')
    op.drop_index('ix_users_is_deleted_created', table_name='users')
    op.drop_index('ix_schools_is_deleted_created', table_name='schools')
