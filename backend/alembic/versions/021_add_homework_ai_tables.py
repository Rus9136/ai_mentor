"""Add homework tables with AI integration support

Revision ID: 021
Revises: 020
Create Date: 2025-12-24

This migration creates tables for homework assignments with AI support:
1. homework - Main homework assignment
2. homework_tasks - Individual tasks (linked to paragraphs)
3. homework_task_questions - Questions (AI-generated or static)
4. homework_students - Student assignment tracking
5. student_task_submissions - Task submission tracking
6. student_task_answers - Individual answers with AI grading
7. ai_generation_logs - AI operation logging for auditing
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '021'
down_revision: Union[str, None] = 'f12834ad84b5'  # Changed from 020 to fix branch
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM types
    homework_status_enum = postgresql.ENUM(
        'draft', 'published', 'closed', 'archived',
        name='homework_status_enum',
        create_type=False
    )
    homework_status_enum.create(op.get_bind(), checkfirst=True)

    homework_task_type_enum = postgresql.ENUM(
        'read', 'quiz', 'open_question', 'essay', 'practice', 'code',
        name='homework_task_type_enum',
        create_type=False
    )
    homework_task_type_enum.create(op.get_bind(), checkfirst=True)

    homework_question_type_enum = postgresql.ENUM(
        'single_choice', 'multiple_choice', 'true_false', 'short_answer', 'open_ended', 'code',
        name='homework_question_type_enum',
        create_type=False
    )
    homework_question_type_enum.create(op.get_bind(), checkfirst=True)

    homework_student_status_enum = postgresql.ENUM(
        'assigned', 'in_progress', 'submitted', 'graded', 'returned',
        name='homework_student_status_enum',
        create_type=False
    )
    homework_student_status_enum.create(op.get_bind(), checkfirst=True)

    task_submission_status_enum = postgresql.ENUM(
        'not_started', 'in_progress', 'submitted', 'graded',
        name='task_submission_status_enum',
        create_type=False
    )
    task_submission_status_enum.create(op.get_bind(), checkfirst=True)

    bloom_level_enum = postgresql.ENUM(
        'remember', 'understand', 'apply', 'analyze', 'evaluate', 'create',
        name='bloom_level_enum',
        create_type=False
    )
    bloom_level_enum.create(op.get_bind(), checkfirst=True)

    ai_operation_type_enum = postgresql.ENUM(
        'question_generation', 'answer_grading', 'feedback_generation', 'personalization',
        name='ai_operation_type_enum',
        create_type=False
    )
    ai_operation_type_enum.create(op.get_bind(), checkfirst=True)

    # =========================================================================
    # 1. homework - Main homework assignment table
    # =========================================================================
    op.create_table(
        'homework',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        # Relationships
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),
        sa.Column('class_id', sa.Integer(), sa.ForeignKey('school_classes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('teachers.id', ondelete='CASCADE'), nullable=False),

        # Basic info
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),

        # Time management
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('due_date', sa.DateTime(timezone=True), nullable=False),
        sa.Column('late_submission_allowed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('late_penalty_percent', sa.Integer(), nullable=False, server_default='0'),

        # AI settings
        sa.Column('ai_generation_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('target_difficulty', sa.String(20), nullable=False, server_default='auto'),
        sa.Column('personalization_enabled', sa.Boolean(), nullable=False, server_default='true'),

        # Grading settings
        sa.Column('auto_check_enabled', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('ai_check_enabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('show_answers_after', sa.String(20), nullable=False, server_default='submission'),
        sa.Column('show_explanations', sa.Boolean(), nullable=False, server_default='true'),

        # Status
        sa.Column('status', homework_status_enum, nullable=False, server_default='draft'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),

        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('late_penalty_percent >= 0 AND late_penalty_percent <= 100', name='ck_late_penalty_range'),
    )

    op.create_index('idx_homework_school_id', 'homework', ['school_id'])
    op.create_index('idx_homework_class_id', 'homework', ['class_id'])
    op.create_index('idx_homework_teacher_id', 'homework', ['teacher_id'])
    op.create_index('idx_homework_school_class', 'homework', ['school_id', 'class_id'])
    op.create_index('idx_homework_due_date_status', 'homework', ['due_date', 'status'])
    op.create_index('idx_homework_status', 'homework', ['status'])

    # =========================================================================
    # 2. homework_tasks - Individual tasks within homework
    # =========================================================================
    op.create_table(
        'homework_tasks',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('homework_id', sa.Integer(), sa.ForeignKey('homework.id', ondelete='CASCADE'), nullable=False),

        # Content links
        sa.Column('paragraph_id', sa.Integer(), sa.ForeignKey('paragraphs.id', ondelete='SET NULL'), nullable=True),
        sa.Column('chapter_id', sa.Integer(), sa.ForeignKey('chapters.id', ondelete='SET NULL'), nullable=True),
        sa.Column('learning_outcome_id', sa.Integer(), sa.ForeignKey('learning_outcomes.id', ondelete='SET NULL'), nullable=True),

        # Task configuration
        sa.Column('task_type', homework_task_type_enum, nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('points', sa.Integer(), nullable=False, server_default='10'),
        sa.Column('time_limit_minutes', sa.Integer(), nullable=True),

        # AI generation
        sa.Column('ai_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ai_prompt_template', sa.Text(), nullable=True),
        sa.Column('generation_params', postgresql.JSONB(astext_type=sa.Text()), nullable=False, server_default='{}'),

        # Static content
        sa.Column('static_content', sa.Text(), nullable=True),
        sa.Column('static_question_ids', postgresql.ARRAY(sa.Integer()), nullable=True),

        # Instructions
        sa.Column('instructions', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_homework_task_homework', 'homework_tasks', ['homework_id', 'sort_order'])
    op.create_index('idx_homework_task_paragraph', 'homework_tasks', ['paragraph_id'])
    op.create_index('idx_homework_task_chapter', 'homework_tasks', ['chapter_id'])

    # =========================================================================
    # 3. homework_task_questions - Questions within tasks
    # =========================================================================
    op.create_table(
        'homework_task_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('homework_task_id', sa.Integer(), sa.ForeignKey('homework_tasks.id', ondelete='CASCADE'), nullable=False),

        # Question content
        sa.Column('question_type', homework_question_type_enum, nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_html', sa.Text(), nullable=True),

        # Answer options (closed questions)
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('correct_answer', sa.Text(), nullable=True),
        sa.Column('answer_pattern', sa.String(500), nullable=True),

        # AI grading (open questions)
        sa.Column('grading_rubric', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('expected_answer_hints', sa.Text(), nullable=True),
        sa.Column('ai_grading_prompt', sa.Text(), nullable=True),

        # Metadata
        sa.Column('points', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('difficulty', sa.String(20), nullable=True),
        sa.Column('bloom_level', bloom_level_enum, nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),

        # AI generation metadata
        sa.Column('ai_generated', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('generation_model', sa.String(100), nullable=True),
        sa.Column('generation_metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        sa.PrimaryKeyConstraint('id'),
    )

    op.create_index('idx_homework_question_task', 'homework_task_questions', ['homework_task_id', 'sort_order'])

    # =========================================================================
    # 4. homework_students - Student assignment tracking
    # =========================================================================
    op.create_table(
        'homework_students',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('homework_id', sa.Integer(), sa.ForeignKey('homework.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),

        # Personalization
        sa.Column('assigned_difficulty', sa.String(20), nullable=True),
        sa.Column('mastery_level_at_assign', sa.String(1), nullable=True),
        sa.Column('personalized_task_ids', postgresql.ARRAY(sa.Integer()), nullable=True),

        # Status
        sa.Column('status', homework_student_status_enum, nullable=False, server_default='assigned'),

        # Timestamps
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('graded_at', sa.DateTime(timezone=True), nullable=True),

        # Results
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('percentage', sa.Float(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),

        # AI grading
        sa.Column('ai_graded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('teacher_reviewed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('teacher_adjusted_score', sa.Float(), nullable=True),
        sa.Column('teacher_feedback', sa.Text(), nullable=True),

        # Additional
        sa.Column('submission_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('late_submitted', sa.Boolean(), nullable=False, server_default='false'),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('homework_id', 'student_id', name='uq_homework_student'),
    )

    op.create_index('idx_homework_student_homework', 'homework_students', ['homework_id'])
    op.create_index('idx_homework_student_student', 'homework_students', ['student_id'])
    op.create_index('idx_homework_student_school', 'homework_students', ['school_id', 'student_id'])
    op.create_index('idx_homework_student_status', 'homework_students', ['status'])

    # =========================================================================
    # 5. student_task_submissions - Task submission tracking
    # =========================================================================
    op.create_table(
        'student_task_submissions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('homework_student_id', sa.Integer(), sa.ForeignKey('homework_students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('homework_task_id', sa.Integer(), sa.ForeignKey('homework_tasks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),

        # Status
        sa.Column('status', task_submission_status_enum, nullable=False, server_default='not_started'),

        # Results
        sa.Column('score', sa.Float(), nullable=True),
        sa.Column('max_score', sa.Float(), nullable=True),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=False, server_default='0'),

        # AI grading
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('ai_graded_at', sa.DateTime(timezone=True), nullable=True),

        # Timestamps
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('submitted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('attempt_number', sa.Integer(), nullable=False, server_default='1'),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('homework_student_id', 'homework_task_id', 'attempt_number', name='uq_task_submission_attempt'),
    )

    op.create_index('idx_task_submission_homework_student', 'student_task_submissions', ['homework_student_id'])
    op.create_index('idx_task_submission_task', 'student_task_submissions', ['homework_task_id'])
    op.create_index('idx_task_submission_student', 'student_task_submissions', ['student_id', 'school_id'])

    # =========================================================================
    # 6. student_task_answers - Individual answers
    # =========================================================================
    op.create_table(
        'student_task_answers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'),

        sa.Column('submission_id', sa.Integer(), sa.ForeignKey('student_task_submissions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('question_id', sa.Integer(), sa.ForeignKey('homework_task_questions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='CASCADE'), nullable=False),
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='CASCADE'), nullable=False),

        # Answer content
        sa.Column('answer_type', sa.String(30), nullable=True),
        sa.Column('selected_option_ids', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('answer_text', sa.Text(), nullable=True),
        sa.Column('answer_code', sa.Text(), nullable=True),
        sa.Column('answer_file_url', sa.String(500), nullable=True),

        # Auto-grading (closed questions)
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('partial_score', sa.Float(), nullable=True),

        # AI grading (open questions)
        sa.Column('ai_score', sa.Float(), nullable=True),
        sa.Column('ai_confidence', sa.Float(), nullable=True),
        sa.Column('ai_feedback', sa.Text(), nullable=True),
        sa.Column('ai_rubric_scores', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ai_grading_model', sa.String(100), nullable=True),
        sa.Column('ai_graded_at', sa.DateTime(timezone=True), nullable=True),

        # Teacher override
        sa.Column('teacher_override_score', sa.Float(), nullable=True),
        sa.Column('teacher_comment', sa.Text(), nullable=True),
        sa.Column('flagged_for_review', sa.Boolean(), nullable=False, server_default='false'),

        # Metadata
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('time_spent_seconds', sa.Integer(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('submission_id', 'question_id', name='uq_answer_submission_question'),
    )

    op.create_index('idx_answer_submission', 'student_task_answers', ['submission_id'])
    op.create_index('idx_answer_question', 'student_task_answers', ['question_id'])
    op.create_index('idx_answer_student', 'student_task_answers', ['student_id', 'school_id'])
    op.create_index(
        'idx_answer_flagged',
        'student_task_answers',
        ['flagged_for_review'],
        postgresql_where=sa.text('flagged_for_review = true')
    )

    # =========================================================================
    # 7. ai_generation_logs - AI operation logging
    # =========================================================================
    op.create_table(
        'ai_generation_logs',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),

        # Context
        sa.Column('school_id', sa.Integer(), sa.ForeignKey('schools.id', ondelete='SET NULL'), nullable=True),
        sa.Column('teacher_id', sa.Integer(), sa.ForeignKey('teachers.id', ondelete='SET NULL'), nullable=True),
        sa.Column('homework_id', sa.Integer(), sa.ForeignKey('homework.id', ondelete='SET NULL'), nullable=True),
        sa.Column('homework_task_id', sa.Integer(), sa.ForeignKey('homework_tasks.id', ondelete='SET NULL'), nullable=True),
        sa.Column('student_id', sa.Integer(), sa.ForeignKey('students.id', ondelete='SET NULL'), nullable=True),

        # Operation
        sa.Column('operation_type', ai_operation_type_enum, nullable=False),

        # Input
        sa.Column('input_context', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('prompt_used', sa.Text(), nullable=True),

        # Output
        sa.Column('model_used', sa.String(100), nullable=True),
        sa.Column('raw_response', sa.Text(), nullable=True),
        sa.Column('parsed_output', postgresql.JSONB(astext_type=sa.Text()), nullable=True),

        # Metrics
        sa.Column('tokens_input', sa.Integer(), nullable=True),
        sa.Column('tokens_output', sa.Integer(), nullable=True),
        sa.Column('latency_ms', sa.Integer(), nullable=True),
        sa.Column('cost_usd', sa.Float(), nullable=True),

        # Quality
        sa.Column('success', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('human_rating', sa.Integer(), nullable=True),
        sa.Column('human_feedback', sa.Text(), nullable=True),

        sa.PrimaryKeyConstraint('id'),
        sa.CheckConstraint('human_rating IS NULL OR (human_rating >= 1 AND human_rating <= 5)', name='ck_human_rating_range'),
    )

    op.create_index('idx_ai_log_operation_date', 'ai_generation_logs', ['operation_type', 'created_at'])
    op.create_index('idx_ai_log_school', 'ai_generation_logs', ['school_id', 'created_at'])
    op.create_index('idx_ai_log_operation_type', 'ai_generation_logs', ['operation_type'])

    # =========================================================================
    # RLS Policies for homework tables
    # =========================================================================

    # Enable RLS on all tables
    tables_with_school_id = [
        'homework',
        'homework_students',
        'student_task_submissions',
        'student_task_answers',
        'ai_generation_logs',
    ]

    for table in tables_with_school_id:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY")

        # App user policy (school isolation)
        op.execute(f"""
            CREATE POLICY {table}_school_isolation ON {table}
            FOR ALL
            TO ai_mentor_app
            USING (
                school_id = COALESCE(NULLIF(current_setting('app.current_school_id', true), ''), '0')::INTEGER
                OR school_id IS NULL
            )
        """)

        # Superuser bypass
        op.execute(f"""
            CREATE POLICY {table}_superuser ON {table}
            FOR ALL
            TO ai_mentor_user
            USING (true)
            WITH CHECK (true)
        """)

    # Tables without school_id (inherit from parent)
    op.execute("ALTER TABLE homework_tasks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE homework_tasks FORCE ROW LEVEL SECURITY")
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
    op.execute("""
        CREATE POLICY homework_tasks_superuser ON homework_tasks
        FOR ALL
        TO ai_mentor_user
        USING (true)
        WITH CHECK (true)
    """)

    op.execute("ALTER TABLE homework_task_questions ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE homework_task_questions FORCE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY homework_task_questions_school_isolation ON homework_task_questions
        FOR ALL
        TO ai_mentor_app
        USING (
            EXISTS (
                SELECT 1 FROM homework_tasks ht
                JOIN homework h ON h.id = ht.homework_id
                WHERE ht.id = homework_task_questions.homework_task_id
                AND h.school_id = COALESCE(NULLIF(current_setting('app.current_school_id', true), ''), '0')::INTEGER
            )
        )
    """)
    op.execute("""
        CREATE POLICY homework_task_questions_superuser ON homework_task_questions
        FOR ALL
        TO ai_mentor_user
        USING (true)
        WITH CHECK (true)
    """)


def downgrade() -> None:
    # Drop RLS policies
    tables = [
        'homework',
        'homework_tasks',
        'homework_task_questions',
        'homework_students',
        'student_task_submissions',
        'student_task_answers',
        'ai_generation_logs',
    ]

    for table in tables:
        op.execute(f"DROP POLICY IF EXISTS {table}_school_isolation ON {table}")
        op.execute(f"DROP POLICY IF EXISTS {table}_superuser ON {table}")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY")

    # Drop tables in reverse order (respect foreign keys)
    op.drop_table('ai_generation_logs')
    op.drop_table('student_task_answers')
    op.drop_table('student_task_submissions')
    op.drop_table('homework_students')
    op.drop_table('homework_task_questions')
    op.drop_table('homework_tasks')
    op.drop_table('homework')

    # Drop ENUM types
    op.execute("DROP TYPE IF EXISTS ai_operation_type_enum")
    op.execute("DROP TYPE IF EXISTS bloom_level_enum")
    op.execute("DROP TYPE IF EXISTS task_submission_status_enum")
    op.execute("DROP TYPE IF EXISTS homework_student_status_enum")
    op.execute("DROP TYPE IF EXISTS homework_question_type_enum")
    op.execute("DROP TYPE IF EXISTS homework_task_type_enum")
    op.execute("DROP TYPE IF EXISTS homework_status_enum")
