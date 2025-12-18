"""Add paragraph steps and embedded questions

Revision ID: a1b2c3d4e5f6
Revises: 6e78f4e8e450
Create Date: 2025-12-18 17:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '016'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add new columns to student_paragraphs for step tracking and self-assessment
    op.add_column('student_paragraphs',
        sa.Column('current_step', sa.String(20), nullable=True, server_default='intro')
    )
    op.add_column('student_paragraphs',
        sa.Column('self_assessment', sa.String(20), nullable=True)
    )
    op.add_column('student_paragraphs',
        sa.Column('self_assessment_at', sa.DateTime(timezone=True), nullable=True)
    )

    # 2. Create embedded_questions table
    op.create_table(
        'embedded_questions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('paragraph_id', sa.Integer(), nullable=False),
        sa.Column('question_text', sa.Text(), nullable=False),
        sa.Column('question_type', sa.String(20), nullable=False),  # single_choice, multiple_choice, true_false
        sa.Column('options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('correct_answer', sa.String(255), nullable=True),  # For simple answers
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.Column('hint', sa.Text(), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['paragraph_id'], ['paragraphs.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_embedded_questions_paragraph_id', 'embedded_questions', ['paragraph_id'])

    # 3. Create student_embedded_answers table
    op.create_table(
        'student_embedded_answers',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('question_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('selected_answer', sa.String(255), nullable=True),
        sa.Column('selected_options', postgresql.JSONB(astext_type=sa.Text()), nullable=True),  # For multiple choice
        sa.Column('is_correct', sa.Boolean(), nullable=True),
        sa.Column('attempts_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('answered_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['question_id'], ['embedded_questions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('student_id', 'question_id', name='uq_student_embedded_answer')
    )
    op.create_index('ix_student_embedded_answers_student_id', 'student_embedded_answers', ['student_id'])
    op.create_index('ix_student_embedded_answers_question_id', 'student_embedded_answers', ['question_id'])
    op.create_index('ix_student_embedded_answers_school_id', 'student_embedded_answers', ['school_id'])

    # 4. Add RLS policies for embedded_questions (read through paragraph -> chapter -> textbook)
    op.execute("""
        ALTER TABLE embedded_questions ENABLE ROW LEVEL SECURITY;
        ALTER TABLE embedded_questions FORCE ROW LEVEL SECURITY;

        CREATE POLICY "embedded_questions_read_policy" ON embedded_questions
        FOR SELECT USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = embedded_questions.paragraph_id
                AND (t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
                     OR t.school_id IS NULL)
            )
        );

        CREATE POLICY "embedded_questions_write_policy" ON embedded_questions
        FOR ALL USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR EXISTS (
                SELECT 1 FROM paragraphs p
                JOIN chapters c ON c.id = p.chapter_id
                JOIN textbooks t ON t.id = c.textbook_id
                WHERE p.id = embedded_questions.paragraph_id
                AND t.school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
            )
        );
    """)

    # 5. Add RLS policies for student_embedded_answers
    op.execute("""
        ALTER TABLE student_embedded_answers ENABLE ROW LEVEL SECURITY;
        ALTER TABLE student_embedded_answers FORCE ROW LEVEL SECURITY;

        CREATE POLICY "student_embedded_answers_isolation_policy" ON student_embedded_answers
        FOR ALL USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int
        );
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("""
        DROP POLICY IF EXISTS "student_embedded_answers_isolation_policy" ON student_embedded_answers;
        DROP POLICY IF EXISTS "embedded_questions_write_policy" ON embedded_questions;
        DROP POLICY IF EXISTS "embedded_questions_read_policy" ON embedded_questions;
    """)

    # Drop tables
    op.drop_index('ix_student_embedded_answers_school_id', table_name='student_embedded_answers')
    op.drop_index('ix_student_embedded_answers_question_id', table_name='student_embedded_answers')
    op.drop_index('ix_student_embedded_answers_student_id', table_name='student_embedded_answers')
    op.drop_table('student_embedded_answers')

    op.drop_index('ix_embedded_questions_paragraph_id', table_name='embedded_questions')
    op.drop_table('embedded_questions')

    # Drop columns from student_paragraphs
    op.drop_column('student_paragraphs', 'self_assessment_at')
    op.drop_column('student_paragraphs', 'self_assessment')
    op.drop_column('student_paragraphs', 'current_step')
