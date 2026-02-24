"""Add exercises table and exercise_id to homework_tasks

Revision ID: 032_exercises
Revises: 031_practice_score
Create Date: 2026-02-24
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '032_exercises'
down_revision = '031_practice_score'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create exercises table
    op.create_table(
        'exercises',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('paragraph_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=True),
        sa.Column('exercise_number', sa.String(20), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('difficulty', sa.String(1), nullable=True),
        sa.Column('content_text', sa.Text(), nullable=False),
        sa.Column('content_html', sa.Text(), nullable=True),
        sa.Column('sub_exercises', postgresql.JSONB(), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('answer_html', sa.Text(), nullable=True),
        sa.Column('has_answer', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_starred', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('language', sa.String(5), nullable=False, server_default='kk'),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(['paragraph_id'], ['paragraphs.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('paragraph_id', 'exercise_number', name='uq_exercise_paragraph_number'),
    )
    op.create_index('ix_exercises_id', 'exercises', ['id'])
    op.create_index('ix_exercises_paragraph_id', 'exercises', ['paragraph_id'])
    op.create_index('ix_exercises_school_id', 'exercises', ['school_id'])
    op.create_index('idx_exercise_paragraph_difficulty', 'exercises', ['paragraph_id', 'difficulty'])

    # Add exercise_id to homework_tasks
    op.add_column(
        'homework_tasks',
        sa.Column('exercise_id', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_homework_tasks_exercise_id',
        'homework_tasks', 'exercises',
        ['exercise_id'], ['id'],
        ondelete='SET NULL'
    )
    op.create_index('ix_homework_tasks_exercise_id', 'homework_tasks', ['exercise_id'])


def downgrade() -> None:
    # Remove exercise_id from homework_tasks
    op.drop_index('ix_homework_tasks_exercise_id', table_name='homework_tasks')
    op.drop_constraint('fk_homework_tasks_exercise_id', 'homework_tasks', type_='foreignkey')
    op.drop_column('homework_tasks', 'exercise_id')

    # Drop exercises table
    op.drop_index('idx_exercise_paragraph_difficulty', table_name='exercises')
    op.drop_index('ix_exercises_school_id', table_name='exercises')
    op.drop_index('ix_exercises_paragraph_id', table_name='exercises')
    op.drop_index('ix_exercises_id', table_name='exercises')
    op.drop_table('exercises')
