"""create_mastery_tables

Creates paragraph_mastery and chapter_mastery tables for two-level mastery tracking.

Architecture:
- paragraph_mastery: Fine-grained tracking per lesson/paragraph
- chapter_mastery: Aggregated tracking for A/B/C grouping
- mastery_history: Updated to support both paragraph and chapter changes (polymorphic)

Revision ID: d6cfba8cd6fd
Revises: ea1742b576f3
Create Date: 2025-11-07 08:42:32.900052

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6cfba8cd6fd'
down_revision: Union[str, None] = 'ea1742b576f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create paragraph_mastery table (fine-grained tracking)
    op.create_table(
        'paragraph_mastery',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('paragraph_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),

        # Scores from formative tests
        sa.Column('test_score', sa.Float(), nullable=True),  # Latest test score
        sa.Column('average_score', sa.Float(), nullable=True),  # Average across attempts
        sa.Column('best_score', sa.Float(), nullable=True),  # Best score achieved
        sa.Column('attempts_count', sa.Integer(), nullable=False, server_default='0'),

        # Learning indicators
        sa.Column('time_spent', sa.Integer(), nullable=False, server_default='0'),  # Seconds
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),

        # Status: struggling, progressing, mastered
        sa.Column('status', sa.String(20), nullable=False, server_default='progressing'),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['paragraph_id'], ['paragraphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    )

    # Create indexes for paragraph_mastery
    op.create_index('ix_paragraph_mastery_student_id', 'paragraph_mastery', ['student_id'])
    op.create_index('ix_paragraph_mastery_paragraph_id', 'paragraph_mastery', ['paragraph_id'])
    op.create_index('ix_paragraph_mastery_school_id', 'paragraph_mastery', ['school_id'])
    op.create_index('ix_paragraph_mastery_student_paragraph', 'paragraph_mastery', ['student_id', 'paragraph_id'], unique=True)
    op.create_index('ix_paragraph_mastery_status', 'paragraph_mastery', ['status'])

    # Create chapter_mastery table (aggregated for A/B/C grouping)
    op.create_table(
        'chapter_mastery',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('chapter_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),

        # Aggregated from paragraphs
        sa.Column('total_paragraphs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_paragraphs', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('mastered_paragraphs', sa.Integer(), nullable=False, server_default='0'),  # >= 85%
        sa.Column('struggling_paragraphs', sa.Integer(), nullable=False, server_default='0'),  # < 60%

        # Aggregated scores
        sa.Column('average_score', sa.Float(), nullable=True),  # Average across paragraphs
        sa.Column('weighted_score', sa.Float(), nullable=True),  # Newer paragraphs weighted higher

        # Summative test (final chapter test)
        sa.Column('summative_score', sa.Float(), nullable=True),
        sa.Column('summative_passed', sa.Boolean(), nullable=True),

        # A/B/C Group
        sa.Column('mastery_level', sa.String(1), nullable=False, server_default='C'),  # A, B, or C
        sa.Column('mastery_score', sa.Float(), nullable=False, server_default='0.0'),  # 0-100

        # Progress tracking
        sa.Column('progress_percentage', sa.Integer(), nullable=False, server_default='0'),  # 0-100
        sa.Column('estimated_completion_date', sa.Date(), nullable=True),

        # Timestamps
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),
        sa.Column('last_updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),

        # Primary key
        sa.PrimaryKeyConstraint('id'),

        # Foreign keys
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['chapter_id'], ['chapters.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
    )

    # Create indexes for chapter_mastery
    op.create_index('ix_chapter_mastery_student_id', 'chapter_mastery', ['student_id'])
    op.create_index('ix_chapter_mastery_chapter_id', 'chapter_mastery', ['chapter_id'])
    op.create_index('ix_chapter_mastery_school_id', 'chapter_mastery', ['school_id'])
    op.create_index('ix_chapter_mastery_student_chapter', 'chapter_mastery', ['student_id', 'chapter_id'], unique=True)
    op.create_index('ix_chapter_mastery_level', 'chapter_mastery', ['mastery_level'])

    # Update mastery_history to support polymorphic tracking (both paragraph and chapter)
    # Add chapter_id column (paragraph_id already exists)
    op.add_column('mastery_history', sa.Column('chapter_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_mastery_history_chapter', 'mastery_history', 'chapters', ['chapter_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_mastery_history_chapter_id', 'mastery_history', ['chapter_id'])

    # Add previous_score and new_score columns for tracking changes
    op.add_column('mastery_history', sa.Column('previous_score', sa.Float(), nullable=True))
    op.add_column('mastery_history', sa.Column('new_score', sa.Float(), nullable=True))
    op.add_column('mastery_history', sa.Column('previous_level', sa.String(20), nullable=True))
    op.add_column('mastery_history', sa.Column('new_level', sa.String(20), nullable=True))

    # Add test_attempt_id to track what triggered the change
    op.add_column('mastery_history', sa.Column('test_attempt_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_mastery_history_attempt', 'mastery_history', 'test_attempts', ['test_attempt_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_mastery_history_attempt_id', 'mastery_history', ['test_attempt_id'])


def downgrade() -> None:
    # Drop mastery_history updates
    op.drop_index('ix_mastery_history_attempt_id', table_name='mastery_history')
    op.drop_constraint('fk_mastery_history_attempt', 'mastery_history', type_='foreignkey')
    op.drop_column('mastery_history', 'test_attempt_id')

    op.drop_column('mastery_history', 'new_level')
    op.drop_column('mastery_history', 'previous_level')
    op.drop_column('mastery_history', 'new_score')
    op.drop_column('mastery_history', 'previous_score')

    op.drop_index('ix_mastery_history_chapter_id', table_name='mastery_history')
    op.drop_constraint('fk_mastery_history_chapter', 'mastery_history', type_='foreignkey')
    op.drop_column('mastery_history', 'chapter_id')

    # Drop chapter_mastery table
    op.drop_index('ix_chapter_mastery_level', table_name='chapter_mastery')
    op.drop_index('ix_chapter_mastery_student_chapter', table_name='chapter_mastery')
    op.drop_index('ix_chapter_mastery_school_id', table_name='chapter_mastery')
    op.drop_index('ix_chapter_mastery_chapter_id', table_name='chapter_mastery')
    op.drop_index('ix_chapter_mastery_student_id', table_name='chapter_mastery')
    op.drop_table('chapter_mastery')

    # Drop paragraph_mastery table
    op.drop_index('ix_paragraph_mastery_status', table_name='paragraph_mastery')
    op.drop_index('ix_paragraph_mastery_student_paragraph', table_name='paragraph_mastery')
    op.drop_index('ix_paragraph_mastery_school_id', table_name='paragraph_mastery')
    op.drop_index('ix_paragraph_mastery_paragraph_id', table_name='paragraph_mastery')
    op.drop_index('ix_paragraph_mastery_student_id', table_name='paragraph_mastery')
    op.drop_table('paragraph_mastery')
