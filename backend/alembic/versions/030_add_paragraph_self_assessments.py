"""Add paragraph_self_assessments table for self-assessment history

Revision ID: 030_add_paragraph_self_assessments
Revises: 029_add_apple_oauth
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '030_self_assessments'
down_revision = 'c39cb6f883c7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'paragraph_self_assessments',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('paragraph_id', sa.Integer(), sa.ForeignKey('paragraphs.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('rating', sa.String(20), nullable=False),
        sa.Column('mastery_impact', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Individual indexes
    op.create_index('ix_paragraph_self_assessments_student_id', 'paragraph_self_assessments', ['student_id'])
    op.create_index('ix_paragraph_self_assessments_paragraph_id', 'paragraph_self_assessments', ['paragraph_id'])
    op.create_index('ix_paragraph_self_assessments_school_id', 'paragraph_self_assessments', ['school_id'])

    # Composite index for common query: all assessments for a student+paragraph
    op.create_index(
        'ix_paragraph_self_assessments_student_paragraph',
        'paragraph_self_assessments',
        ['student_id', 'paragraph_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_paragraph_self_assessments_student_paragraph', table_name='paragraph_self_assessments')
    op.drop_index('ix_paragraph_self_assessments_school_id', table_name='paragraph_self_assessments')
    op.drop_index('ix_paragraph_self_assessments_paragraph_id', table_name='paragraph_self_assessments')
    op.drop_index('ix_paragraph_self_assessments_student_id', table_name='paragraph_self_assessments')
    op.drop_table('paragraph_self_assessments')
