"""Homework AI v2 improvements

Revision ID: 022
Revises: 021
Create Date: 2026-01-04

This migration adds v2 improvements to the homework system:
1. Late submission policy fields (grace_period_hours, max_late_days)
2. Denormalized school_id in homework_tasks for faster RLS
3. max_attempts for homework_tasks
4. Question versioning (version, is_active, replaced_by_id)
5. Late submission tracking in student_task_submissions
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '022'
down_revision: Union[str, None] = '021'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # 1. homework table - Late submission policy improvements
    # =========================================================================

    # Rename late_penalty_percent to late_penalty_per_day
    op.alter_column('homework', 'late_penalty_percent',
                    new_column_name='late_penalty_per_day')

    # Add grace_period_hours
    op.add_column('homework',
        sa.Column('grace_period_hours', sa.Integer(), nullable=False, server_default='0'))

    # Add max_late_days
    op.add_column('homework',
        sa.Column('max_late_days', sa.Integer(), nullable=False, server_default='7'))

    # Add check constraints
    op.create_check_constraint(
        'ck_grace_period_range',
        'homework',
        'grace_period_hours >= 0 AND grace_period_hours <= 168'
    )
    op.create_check_constraint(
        'ck_max_late_days_range',
        'homework',
        'max_late_days >= 0 AND max_late_days <= 30'
    )

    # =========================================================================
    # 2. homework_tasks - Add school_id for RLS without JOIN
    # =========================================================================

    # Add school_id column (nullable first for data migration)
    op.add_column('homework_tasks',
        sa.Column('school_id', sa.Integer(), nullable=True))

    # Populate school_id from homework table
    op.execute("""
        UPDATE homework_tasks ht
        SET school_id = h.school_id
        FROM homework h
        WHERE ht.homework_id = h.id
    """)

    # Make school_id NOT NULL and add FK
    op.alter_column('homework_tasks', 'school_id', nullable=False)
    op.create_foreign_key(
        'fk_homework_tasks_school_id',
        'homework_tasks',
        'schools',
        ['school_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # Add max_attempts
    op.add_column('homework_tasks',
        sa.Column('max_attempts', sa.Integer(), nullable=False, server_default='1'))

    # Add constraints and index
    op.create_check_constraint(
        'ck_max_attempts_range',
        'homework_tasks',
        'max_attempts >= 1 AND max_attempts <= 10'
    )
    op.create_index('idx_homework_task_school', 'homework_tasks', ['school_id'])

    # =========================================================================
    # 3. homework_task_questions - Versioning support
    # =========================================================================

    op.add_column('homework_task_questions',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1'))

    op.add_column('homework_task_questions',
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))

    op.add_column('homework_task_questions',
        sa.Column('replaced_by_id', sa.Integer(), nullable=True))

    # Self-referential FK for version chain
    op.create_foreign_key(
        'fk_question_replaced_by',
        'homework_task_questions',
        'homework_task_questions',
        ['replaced_by_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Index for efficient active question lookup
    op.create_index(
        'idx_questions_active_version',
        'homework_task_questions',
        ['homework_task_id', 'is_active', 'version']
    )

    # =========================================================================
    # 4. student_task_submissions - Late submission tracking
    # =========================================================================

    op.add_column('student_task_submissions',
        sa.Column('is_late', sa.Boolean(), nullable=False, server_default='false'))

    op.add_column('student_task_submissions',
        sa.Column('late_penalty_applied', sa.Float(), nullable=False, server_default='0'))

    op.add_column('student_task_submissions',
        sa.Column('original_score', sa.Float(), nullable=True))

    op.create_check_constraint(
        'ck_late_penalty_applied_range',
        'student_task_submissions',
        'late_penalty_applied >= 0 AND late_penalty_applied <= 100'
    )

    # =========================================================================
    # 5. Update RLS policy for homework_tasks (now with school_id)
    # =========================================================================

    # Drop old policy that uses JOIN
    op.execute("DROP POLICY IF EXISTS homework_tasks_school_isolation ON homework_tasks")

    # Create new policy that uses direct school_id
    op.execute("""
        CREATE POLICY homework_tasks_school_isolation ON homework_tasks
        FOR ALL
        TO ai_mentor_app
        USING (
            school_id = COALESCE(NULLIF(current_setting('app.current_school_id', true), ''), '0')::INTEGER
        )
    """)


def downgrade() -> None:
    # =========================================================================
    # Reverse all changes
    # =========================================================================

    # 5. Restore old RLS policy
    op.execute("DROP POLICY IF EXISTS homework_tasks_school_isolation ON homework_tasks")
    op.execute("""
        CREATE POLICY homework_tasks_school_isolation ON homework_tasks
        FOR ALL
        TO ai_mentor_app
        USING (
            EXISTS (
                SELECT 1 FROM homework h
                WHERE h.id = homework_tasks.homework_id
                AND h.school_id = COALESCE(NULLIF(current_setting('app.current_school_id', true), ''), '0')::INTEGER
            )
        )
    """)

    # 4. student_task_submissions
    op.drop_constraint('ck_late_penalty_applied_range', 'student_task_submissions', type_='check')
    op.drop_column('student_task_submissions', 'original_score')
    op.drop_column('student_task_submissions', 'late_penalty_applied')
    op.drop_column('student_task_submissions', 'is_late')

    # 3. homework_task_questions
    op.drop_index('idx_questions_active_version', 'homework_task_questions')
    op.drop_constraint('fk_question_replaced_by', 'homework_task_questions', type_='foreignkey')
    op.drop_column('homework_task_questions', 'replaced_by_id')
    op.drop_column('homework_task_questions', 'is_active')
    op.drop_column('homework_task_questions', 'version')

    # 2. homework_tasks
    op.drop_index('idx_homework_task_school', 'homework_tasks')
    op.drop_constraint('ck_max_attempts_range', 'homework_tasks', type_='check')
    op.drop_column('homework_tasks', 'max_attempts')
    op.drop_constraint('fk_homework_tasks_school_id', 'homework_tasks', type_='foreignkey')
    op.drop_column('homework_tasks', 'school_id')

    # 1. homework
    op.drop_constraint('ck_max_late_days_range', 'homework', type_='check')
    op.drop_constraint('ck_grace_period_range', 'homework', type_='check')
    op.drop_column('homework', 'max_late_days')
    op.drop_column('homework', 'grace_period_hours')
    op.alter_column('homework', 'late_penalty_per_day',
                    new_column_name='late_penalty_percent')
