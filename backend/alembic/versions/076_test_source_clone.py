"""
Add source_test_id to tests table for clone/adapt feature.

Teachers can clone global tests into school-specific copies.
source_test_id tracks which global test was used as the original.

Revision ID: 076_test_source_clone
Revises: 075_class_teacher_subject_homeroom
"""

revision = '076_test_source_clone'
down_revision = '075_class_teacher_subject_homeroom'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('tests', sa.Column(
        'source_test_id', sa.Integer,
        sa.ForeignKey('tests.id', ondelete='SET NULL'),
        nullable=True
    ))
    op.create_index('ix_tests_source_test_id', 'tests', ['source_test_id'])


def downgrade():
    op.drop_index('ix_tests_source_test_id', table_name='tests')
    op.drop_column('tests', 'source_test_id')
