"""Add school_id to progress tables for data isolation

Revision ID: 008
Revises: 007
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '008'
down_revision: Union[str, None] = '007'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add school_id to all progress tracking tables for better data isolation and performance.

    Changes:
    1. Add school_id to progress tables (nullable first, will be filled then made NOT NULL)
    2. Make textbooks.school_id nullable for global/school content
    3. Add school_id to tests for global/school tests
    4. Add hybrid model fields to textbooks
    """

    # === 1. Add school_id to progress tables (nullable first) ===

    # test_attempts
    op.add_column('test_attempts', sa.Column('school_id', sa.Integer(), nullable=True))

    # mastery_history
    op.add_column('mastery_history', sa.Column('school_id', sa.Integer(), nullable=True))

    # adaptive_groups
    op.add_column('adaptive_groups', sa.Column('school_id', sa.Integer(), nullable=True))

    # student_paragraphs
    op.add_column('student_paragraphs', sa.Column('school_id', sa.Integer(), nullable=True))

    # learning_sessions
    op.add_column('learning_sessions', sa.Column('school_id', sa.Integer(), nullable=True))

    # learning_activities
    op.add_column('learning_activities', sa.Column('school_id', sa.Integer(), nullable=True))

    # analytics_events
    op.add_column('analytics_events', sa.Column('school_id', sa.Integer(), nullable=True))

    # sync_queue
    op.add_column('sync_queue', sa.Column('school_id', sa.Integer(), nullable=True))


    # === 2. Fill school_id from students table ===

    # test_attempts
    op.execute("""
        UPDATE test_attempts
        SET school_id = (SELECT school_id FROM students WHERE students.id = test_attempts.student_id)
        WHERE student_id IS NOT NULL
    """)

    # mastery_history
    op.execute("""
        UPDATE mastery_history
        SET school_id = (SELECT school_id FROM students WHERE students.id = mastery_history.student_id)
        WHERE student_id IS NOT NULL
    """)

    # adaptive_groups
    op.execute("""
        UPDATE adaptive_groups
        SET school_id = (SELECT school_id FROM students WHERE students.id = adaptive_groups.student_id)
        WHERE student_id IS NOT NULL
    """)

    # student_paragraphs
    op.execute("""
        UPDATE student_paragraphs
        SET school_id = (SELECT school_id FROM students WHERE students.id = student_paragraphs.student_id)
        WHERE student_id IS NOT NULL
    """)

    # learning_sessions
    op.execute("""
        UPDATE learning_sessions
        SET school_id = (SELECT school_id FROM students WHERE students.id = learning_sessions.student_id)
        WHERE student_id IS NOT NULL
    """)

    # learning_activities
    op.execute("""
        UPDATE learning_activities
        SET school_id = (SELECT school_id FROM students WHERE students.id = learning_activities.student_id)
        WHERE student_id IS NOT NULL
    """)

    # analytics_events (can be nullable - some events may not be tied to a student)
    op.execute("""
        UPDATE analytics_events
        SET school_id = (SELECT school_id FROM students WHERE students.id = analytics_events.student_id)
        WHERE student_id IS NOT NULL
    """)

    # sync_queue
    op.execute("""
        UPDATE sync_queue
        SET school_id = (SELECT school_id FROM students WHERE students.id = sync_queue.student_id)
        WHERE student_id IS NOT NULL
    """)


    # === 3. Make school_id NOT NULL (except analytics_events) ===

    op.alter_column('test_attempts', 'school_id', nullable=False)
    op.alter_column('mastery_history', 'school_id', nullable=False)
    op.alter_column('adaptive_groups', 'school_id', nullable=False)
    op.alter_column('student_paragraphs', 'school_id', nullable=False)
    op.alter_column('learning_sessions', 'school_id', nullable=False)
    op.alter_column('learning_activities', 'school_id', nullable=False)
    # analytics_events.school_id stays nullable
    op.alter_column('sync_queue', 'school_id', nullable=False)


    # === 4. Add foreign keys ===

    op.create_foreign_key('fk_test_attempts_school', 'test_attempts', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_mastery_history_school', 'mastery_history', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_adaptive_groups_school', 'adaptive_groups', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_student_paragraphs_school', 'student_paragraphs', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_learning_sessions_school', 'learning_sessions', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_learning_activities_school', 'learning_activities', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_analytics_events_school', 'analytics_events', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_foreign_key('fk_sync_queue_school', 'sync_queue', 'schools', ['school_id'], ['id'], ondelete='CASCADE')


    # === 5. Create indexes for performance ===

    # Single column indexes
    op.create_index('ix_test_attempts_school_id', 'test_attempts', ['school_id'])
    op.create_index('ix_mastery_history_school_id', 'mastery_history', ['school_id'])
    op.create_index('ix_adaptive_groups_school_id', 'adaptive_groups', ['school_id'])
    op.create_index('ix_student_paragraphs_school_id', 'student_paragraphs', ['school_id'])
    op.create_index('ix_learning_sessions_school_id', 'learning_sessions', ['school_id'])
    op.create_index('ix_learning_activities_school_id', 'learning_activities', ['school_id'])
    op.create_index('ix_analytics_events_school_id', 'analytics_events', ['school_id'])
    op.create_index('ix_sync_queue_school_id', 'sync_queue', ['school_id'])

    # Composite indexes for common queries
    op.create_index('ix_test_attempts_school_student', 'test_attempts', ['school_id', 'student_id'])
    op.create_index('ix_test_attempts_school_created', 'test_attempts', ['school_id', 'created_at'])
    op.create_index('ix_mastery_history_school_student', 'mastery_history', ['school_id', 'student_id'])
    op.create_index('ix_mastery_history_school_paragraph', 'mastery_history', ['school_id', 'paragraph_id'])
    op.create_index('ix_adaptive_groups_school_student', 'adaptive_groups', ['school_id', 'student_id'])
    op.create_index('ix_student_paragraphs_school_student', 'student_paragraphs', ['school_id', 'student_id'])
    op.create_index('ix_learning_sessions_school_start', 'learning_sessions', ['school_id', 'session_start'])
    op.create_index('ix_learning_activities_school_timestamp', 'learning_activities', ['school_id', 'activity_timestamp'])
    op.create_index('ix_learning_activities_school_type', 'learning_activities', ['school_id', 'activity_type'])
    op.create_index('ix_analytics_events_school_timestamp', 'analytics_events', ['school_id', 'event_timestamp'])
    op.create_index('ix_sync_queue_school_status', 'sync_queue', ['school_id', 'status'])


    # === 6. Add CHECK constraints for data consistency ===

    op.create_check_constraint(
        'check_test_attempts_school',
        'test_attempts',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_mastery_history_school',
        'mastery_history',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_adaptive_groups_school',
        'adaptive_groups',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_student_paragraphs_school',
        'student_paragraphs',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_learning_sessions_school',
        'learning_sessions',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_learning_activities_school',
        'learning_activities',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_analytics_events_school',
        'analytics_events',
        'student_id IS NULL OR school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )

    op.create_check_constraint(
        'check_sync_queue_school',
        'sync_queue',
        'school_id = (SELECT school_id FROM students WHERE id = student_id)'
    )


    # === 7. Make textbooks.school_id nullable for hybrid model ===

    op.alter_column('textbooks', 'school_id', nullable=True)

    # Add fields for hybrid model
    op.add_column('textbooks', sa.Column('global_textbook_id', sa.Integer(), nullable=True))
    op.add_column('textbooks', sa.Column('is_customized', sa.Boolean(), nullable=False, server_default='false'))

    op.create_foreign_key('fk_textbooks_global', 'textbooks', 'textbooks', ['global_textbook_id'], ['id'], ondelete='SET NULL')
    op.create_index('ix_textbooks_global_textbook_id', 'textbooks', ['global_textbook_id'])
    op.create_index('ix_textbooks_school_global', 'textbooks', ['school_id', 'global_textbook_id'])


    # === 8. Add school_id to tests (nullable for global tests) ===

    op.add_column('tests', sa.Column('school_id', sa.Integer(), nullable=True))
    op.create_foreign_key('fk_tests_school', 'tests', 'schools', ['school_id'], ['id'], ondelete='CASCADE')
    op.create_index('ix_tests_school_id', 'tests', ['school_id'])


def downgrade() -> None:
    """Rollback the changes."""

    # Remove school_id from tests
    op.drop_index('ix_tests_school_id', 'tests')
    op.drop_constraint('fk_tests_school', 'tests', type_='foreignkey')
    op.drop_column('tests', 'school_id')

    # Remove hybrid model fields from textbooks
    op.drop_index('ix_textbooks_school_global', 'textbooks')
    op.drop_index('ix_textbooks_global_textbook_id', 'textbooks')
    op.drop_constraint('fk_textbooks_global', 'textbooks', type_='foreignkey')
    op.drop_column('textbooks', 'is_customized')
    op.drop_column('textbooks', 'global_textbook_id')
    op.alter_column('textbooks', 'school_id', nullable=False)

    # Remove CHECK constraints
    op.drop_constraint('check_sync_queue_school', 'sync_queue')
    op.drop_constraint('check_analytics_events_school', 'analytics_events')
    op.drop_constraint('check_learning_activities_school', 'learning_activities')
    op.drop_constraint('check_learning_sessions_school', 'learning_sessions')
    op.drop_constraint('check_student_paragraphs_school', 'student_paragraphs')
    op.drop_constraint('check_adaptive_groups_school', 'adaptive_groups')
    op.drop_constraint('check_mastery_history_school', 'mastery_history')
    op.drop_constraint('check_test_attempts_school', 'test_attempts')

    # Remove composite indexes
    op.drop_index('ix_sync_queue_school_status', 'sync_queue')
    op.drop_index('ix_analytics_events_school_timestamp', 'analytics_events')
    op.drop_index('ix_learning_activities_school_type', 'learning_activities')
    op.drop_index('ix_learning_activities_school_timestamp', 'learning_activities')
    op.drop_index('ix_learning_sessions_school_start', 'learning_sessions')
    op.drop_index('ix_student_paragraphs_school_student', 'student_paragraphs')
    op.drop_index('ix_adaptive_groups_school_student', 'adaptive_groups')
    op.drop_index('ix_mastery_history_school_paragraph', 'mastery_history')
    op.drop_index('ix_mastery_history_school_student', 'mastery_history')
    op.drop_index('ix_test_attempts_school_created', 'test_attempts')
    op.drop_index('ix_test_attempts_school_student', 'test_attempts')

    # Remove single column indexes
    op.drop_index('ix_sync_queue_school_id', 'sync_queue')
    op.drop_index('ix_analytics_events_school_id', 'analytics_events')
    op.drop_index('ix_learning_activities_school_id', 'learning_activities')
    op.drop_index('ix_learning_sessions_school_id', 'learning_sessions')
    op.drop_index('ix_student_paragraphs_school_id', 'student_paragraphs')
    op.drop_index('ix_adaptive_groups_school_id', 'adaptive_groups')
    op.drop_index('ix_mastery_history_school_id', 'mastery_history')
    op.drop_index('ix_test_attempts_school_id', 'test_attempts')

    # Remove foreign keys
    op.drop_constraint('fk_sync_queue_school', 'sync_queue', type_='foreignkey')
    op.drop_constraint('fk_analytics_events_school', 'analytics_events', type_='foreignkey')
    op.drop_constraint('fk_learning_activities_school', 'learning_activities', type_='foreignkey')
    op.drop_constraint('fk_learning_sessions_school', 'learning_sessions', type_='foreignkey')
    op.drop_constraint('fk_student_paragraphs_school', 'student_paragraphs', type_='foreignkey')
    op.drop_constraint('fk_adaptive_groups_school', 'adaptive_groups', type_='foreignkey')
    op.drop_constraint('fk_mastery_history_school', 'mastery_history', type_='foreignkey')
    op.drop_constraint('fk_test_attempts_school', 'test_attempts', type_='foreignkey')

    # Remove school_id columns
    op.drop_column('sync_queue', 'school_id')
    op.drop_column('analytics_events', 'school_id')
    op.drop_column('learning_activities', 'school_id')
    op.drop_column('learning_sessions', 'school_id')
    op.drop_column('student_paragraphs', 'school_id')
    op.drop_column('adaptive_groups', 'school_id')
    op.drop_column('mastery_history', 'school_id')
    op.drop_column('test_attempts', 'school_id')
