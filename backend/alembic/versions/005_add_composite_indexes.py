"""Add composite indexes for query optimization

Revision ID: 005
Revises: 004
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add composite index on test_attempts for "recent attempts by student" queries
    op.create_index(
        'ix_test_attempts_student_created',
        'test_attempts',
        ['student_id', 'created_at'],
        unique=False
    )

    # Add composite index on mastery_history for "student mastery of specific content" queries
    op.create_index(
        'ix_mastery_history_student_paragraph',
        'mastery_history',
        ['student_id', 'paragraph_id'],
        unique=False
    )

    # Add composite index on student_assignments for "assignments by student and status" queries
    op.create_index(
        'ix_student_assignments_student_status',
        'student_assignments',
        ['student_id', 'status'],
        unique=False
    )

    # Add composite index on paragraph_embeddings for efficient embedding lookups
    op.create_index(
        'ix_paragraph_embeddings_paragraph_chunk',
        'paragraph_embeddings',
        ['paragraph_id', 'chunk_index'],
        unique=False
    )


def downgrade() -> None:
    # Remove composite indexes
    op.drop_index('ix_paragraph_embeddings_paragraph_chunk', table_name='paragraph_embeddings')
    op.drop_index('ix_student_assignments_student_status', table_name='student_assignments')
    op.drop_index('ix_mastery_history_student_paragraph', table_name='mastery_history')
    op.drop_index('ix_test_attempts_student_created', table_name='test_attempts')
