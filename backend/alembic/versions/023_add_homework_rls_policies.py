"""Add RLS policies for homework tables

Revision ID: 023
Revises: 022
Create Date: 2026-01-07

This migration:
1. Adds school_id column to homework_task_questions (denormalization for RLS)
2. Fixes incorrect RLS policy in homework_tasks (wrong session variable name)
3. Enables RLS for all 7 homework tables:
   - homework
   - homework_tasks
   - homework_task_questions
   - homework_students
   - student_task_submissions
   - student_task_answers
   - ai_generation_logs
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '023'
down_revision: Union[str, None] = '022'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# RLS policy helpers (consistent with other migrations)
IS_SUPER_ADMIN_SQL = "COALESCE(current_setting('app.is_super_admin', true), 'false') = 'true'"
TENANT_ID_MATCH_SQL = "school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::int"

# Tables with standard RLS (school_id NOT NULL)
STANDARD_RLS_TABLES = [
    'homework',
    'homework_tasks',
    'homework_task_questions',
    'homework_students',
    'student_task_submissions',
    'student_task_answers',
]

# Tables with nullable school_id (special policy)
NULLABLE_RLS_TABLES = [
    'ai_generation_logs',
]


def upgrade() -> None:
    """
    Add RLS policies for homework tables.
    """

    # =========================================================================
    # 1. Add school_id to homework_task_questions (denormalization)
    # =========================================================================

    # Add column as nullable first
    op.add_column('homework_task_questions',
        sa.Column('school_id', sa.Integer(), nullable=True))

    # Populate school_id from homework_tasks
    op.execute("""
        UPDATE homework_task_questions htq
        SET school_id = ht.school_id
        FROM homework_tasks ht
        WHERE htq.homework_task_id = ht.id
    """)

    # Make NOT NULL
    op.alter_column('homework_task_questions', 'school_id', nullable=False)

    # Add FK and index
    op.create_foreign_key(
        'fk_homework_task_questions_school_id',
        'homework_task_questions',
        'schools',
        ['school_id'],
        ['id'],
        ondelete='CASCADE'
    )
    op.create_index('idx_homework_task_questions_school', 'homework_task_questions', ['school_id'])

    # =========================================================================
    # 2. Create trigger for auto-populating school_id on INSERT
    # =========================================================================

    op.execute("""
        CREATE OR REPLACE FUNCTION set_homework_question_school_id()
        RETURNS TRIGGER AS $$
        BEGIN
            IF NEW.school_id IS NULL THEN
                SELECT school_id INTO NEW.school_id
                FROM homework_tasks
                WHERE id = NEW.homework_task_id;
            END IF;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    op.execute("""
        CREATE TRIGGER tr_homework_question_school_id
        BEFORE INSERT ON homework_task_questions
        FOR EACH ROW
        EXECUTE FUNCTION set_homework_question_school_id();
    """)

    # =========================================================================
    # 3. Fix homework_tasks RLS policy (wrong session variable in migration 022)
    # =========================================================================

    # Drop incorrect policy from migration 022
    op.execute("DROP POLICY IF EXISTS homework_tasks_school_isolation ON homework_tasks")

    # =========================================================================
    # 4. Enable RLS and create policies for standard tables
    # =========================================================================

    for table in STANDARD_RLS_TABLES:
        # Enable RLS
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Create isolation policy (SELECT/UPDATE/DELETE)
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL TO PUBLIC
            USING (
                {IS_SUPER_ADMIN_SQL}
                OR {TENANT_ID_MATCH_SQL}
            );
        """)

        # Create insert policy
        op.execute(f"""
            CREATE POLICY tenant_insert_policy ON {table}
            FOR INSERT TO PUBLIC
            WITH CHECK (
                {IS_SUPER_ADMIN_SQL}
                OR {TENANT_ID_MATCH_SQL}
            );
        """)

    # =========================================================================
    # 5. Enable RLS for ai_generation_logs (nullable school_id)
    # =========================================================================

    for table in NULLABLE_RLS_TABLES:
        op.execute(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY;")
        op.execute(f"ALTER TABLE {table} FORCE ROW LEVEL SECURITY;")

        # Special policy: allow NULL school_id (global logs) + own school
        op.execute(f"""
            CREATE POLICY tenant_isolation_policy ON {table}
            FOR ALL TO PUBLIC
            USING (
                {IS_SUPER_ADMIN_SQL}
                OR school_id IS NULL
                OR {TENANT_ID_MATCH_SQL}
            );
        """)

        op.execute(f"""
            CREATE POLICY tenant_insert_policy ON {table}
            FOR INSERT TO PUBLIC
            WITH CHECK (
                {IS_SUPER_ADMIN_SQL}
                OR school_id IS NULL
                OR {TENANT_ID_MATCH_SQL}
            );
        """)


def downgrade() -> None:
    """
    Reverse RLS policies for homework tables.
    """

    # =========================================================================
    # 1. Drop RLS policies
    # =========================================================================

    all_tables = STANDARD_RLS_TABLES + NULLABLE_RLS_TABLES

    for table in all_tables:
        op.execute(f"DROP POLICY IF EXISTS tenant_isolation_policy ON {table};")
        op.execute(f"DROP POLICY IF EXISTS tenant_insert_policy ON {table};")
        op.execute(f"ALTER TABLE {table} DISABLE ROW LEVEL SECURITY;")

    # =========================================================================
    # 2. Restore incorrect homework_tasks policy from migration 022
    # =========================================================================

    op.execute("""
        CREATE POLICY homework_tasks_school_isolation ON homework_tasks
        FOR ALL
        TO ai_mentor_app
        USING (
            school_id = COALESCE(NULLIF(current_setting('app.current_school_id', true), ''), '0')::INTEGER
        );
    """)

    # =========================================================================
    # 3. Remove trigger and function
    # =========================================================================

    op.execute("DROP TRIGGER IF EXISTS tr_homework_question_school_id ON homework_task_questions;")
    op.execute("DROP FUNCTION IF EXISTS set_homework_question_school_id();")

    # =========================================================================
    # 4. Remove school_id from homework_task_questions
    # =========================================================================

    op.drop_index('idx_homework_task_questions_school', 'homework_task_questions')
    op.drop_constraint('fk_homework_task_questions_school_id', 'homework_task_questions', type_='foreignkey')
    op.drop_column('homework_task_questions', 'school_id')
