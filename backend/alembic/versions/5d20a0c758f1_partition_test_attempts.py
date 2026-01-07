"""Partition test_attempts table by started_at (monthly)

Revision ID: 5d20a0c758f1
Revises: 023, add_needs_review_enum
Create Date: 2026-01-07

This migration:
1. Converts test_attempts to a partitioned table (RANGE by started_at)
2. Creates monthly partitions from 2025-01 to 2027-12 (36 partitions)
3. Migrates existing data
4. Recreates indexes and RLS policies
5. Updates test_attempt_answers FK handling

Expected improvements:
- Up to 10x faster queries with date filters
- Easier maintenance (VACUUM per partition)
- Simple archival (DROP old partitions)
"""
from typing import Sequence, Union
from datetime import date

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5d20a0c758f1'
down_revision: Union[str, Sequence[str], None] = ('023', 'add_needs_review_enum')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert test_attempts to partitioned table."""

    # 1. Drop existing RLS policy and indexes first
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempts;
        DROP POLICY IF EXISTS tenant_insert_policy ON test_attempts;
    """)

    # 2. Drop FK from test_attempt_answers (will recreate as index)
    op.execute("""
        ALTER TABLE test_attempt_answers
        DROP CONSTRAINT IF EXISTS test_attempt_answers_attempt_id_fkey;
    """)

    # 3. Rename old table
    op.execute("ALTER TABLE test_attempts RENAME TO test_attempts_old;")

    # 4. Drop old indexes (they reference old table)
    op.execute("""
        DROP INDEX IF EXISTS ix_test_attempts_student_id;
        DROP INDEX IF EXISTS ix_test_attempts_test_id;
        DROP INDEX IF EXISTS ix_test_attempts_school_id;
        DROP INDEX IF EXISTS ix_test_attempts_status;
        DROP INDEX IF EXISTS ix_test_attempts_student_created;
    """)

    # 5. Create new partitioned table with same structure
    # Note: PRIMARY KEY must include the partition key (started_at)
    op.execute("""
        CREATE TABLE test_attempts (
            id SERIAL,
            student_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            score DOUBLE PRECISION,
            points_earned DOUBLE PRECISION,
            total_points DOUBLE PRECISION,
            passed BOOLEAN,
            time_spent INTEGER,
            synced_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, started_at)
        ) PARTITION BY RANGE (started_at);
    """)

    # 6. Create monthly partitions (2025-01 to 2027-12)
    for year in [2025, 2026, 2027]:
        for month in range(1, 13):
            partition_name = f"test_attempts_{year}_{month:02d}"
            start_date = f"{year}-{month:02d}-01"

            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            op.execute(f"""
                CREATE TABLE {partition_name}
                PARTITION OF test_attempts
                FOR VALUES FROM ('{start_date}') TO ('{end_date}');
            """)

    # 7. Create default partition for data outside defined ranges
    op.execute("""
        CREATE TABLE test_attempts_default
        PARTITION OF test_attempts DEFAULT;
    """)

    # 8. Migrate existing data
    op.execute("""
        INSERT INTO test_attempts (
            id, student_id, test_id, school_id, attempt_number, status,
            started_at, completed_at, score, points_earned, total_points,
            passed, time_spent, synced_at, created_at, updated_at
        )
        SELECT
            id, student_id, test_id, school_id, attempt_number, status,
            started_at, completed_at, score, points_earned, total_points,
            passed, time_spent, synced_at, created_at, updated_at
        FROM test_attempts_old;
    """)

    # 9. Reset sequence for id to max + 1
    op.execute("""
        SELECT setval('test_attempts_id_seq',
            COALESCE((SELECT MAX(id) FROM test_attempts), 0) + 1, false);
    """)

    # 10. Create indexes (will be created on each partition automatically)
    op.execute("""
        CREATE INDEX ix_test_attempts_student_id ON test_attempts(student_id);
        CREATE INDEX ix_test_attempts_test_id ON test_attempts(test_id);
        CREATE INDEX ix_test_attempts_school_id ON test_attempts(school_id);
        CREATE INDEX ix_test_attempts_status ON test_attempts(status);
        CREATE INDEX ix_test_attempts_student_created ON test_attempts(student_id, created_at);
        CREATE INDEX ix_test_attempts_started_at ON test_attempts(started_at);
    """)

    # 11. Add foreign keys to parent table
    op.execute("""
        ALTER TABLE test_attempts
        ADD CONSTRAINT fk_test_attempts_student
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

        ALTER TABLE test_attempts
        ADD CONSTRAINT fk_test_attempts_test
        FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;

        ALTER TABLE test_attempts
        ADD CONSTRAINT fk_test_attempts_school
        FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;
    """)

    # 12. Enable RLS on partitioned table (inherits to partitions)
    op.execute("""
        ALTER TABLE test_attempts ENABLE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation_policy ON test_attempts
        FOR ALL USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );

        CREATE POLICY tenant_insert_policy ON test_attempts
        FOR INSERT WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );
    """)

    # 13. Create index on test_attempt_answers for referential integrity check
    op.execute("""
        CREATE INDEX IF NOT EXISTS ix_test_attempt_answers_attempt_id
        ON test_attempt_answers(attempt_id);
    """)

    # 14. Drop old table (CASCADE to remove dependent policies and constraints)
    op.execute("DROP TABLE test_attempts_old CASCADE;")

    # 15. Add comment for documentation
    op.execute("""
        COMMENT ON TABLE test_attempts IS
        'Partitioned by started_at (monthly). Created 2026-01-07.
        Partitions: test_attempts_YYYY_MM for 2025-2027, test_attempts_default for others.
        Note: PRIMARY KEY is (id, started_at) for partition support.';
    """)


def downgrade() -> None:
    """Revert to non-partitioned table."""

    # 1. Drop RLS
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON test_attempts;
        DROP POLICY IF EXISTS tenant_insert_policy ON test_attempts;
    """)

    # 2. Create non-partitioned table
    op.execute("""
        CREATE TABLE test_attempts_new (
            id SERIAL PRIMARY KEY,
            student_id INTEGER NOT NULL,
            test_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            attempt_number INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(20) NOT NULL DEFAULT 'in_progress',
            started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            completed_at TIMESTAMPTZ,
            score DOUBLE PRECISION,
            points_earned DOUBLE PRECISION,
            total_points DOUBLE PRECISION,
            passed BOOLEAN,
            time_spent INTEGER,
            synced_at TIMESTAMPTZ,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # 3. Copy data
    op.execute("""
        INSERT INTO test_attempts_new
        SELECT * FROM test_attempts;
    """)

    # 4. Drop partitioned table and all partitions
    op.execute("DROP TABLE test_attempts CASCADE;")

    # 5. Rename new table
    op.execute("ALTER TABLE test_attempts_new RENAME TO test_attempts;")

    # 6. Reset sequence
    op.execute("""
        SELECT setval('test_attempts_id_seq',
            COALESCE((SELECT MAX(id) FROM test_attempts), 0) + 1, false);
    """)

    # 7. Recreate indexes
    op.execute("""
        CREATE INDEX ix_test_attempts_student_id ON test_attempts(student_id);
        CREATE INDEX ix_test_attempts_test_id ON test_attempts(test_id);
        CREATE INDEX ix_test_attempts_school_id ON test_attempts(school_id);
        CREATE INDEX ix_test_attempts_status ON test_attempts(status);
        CREATE INDEX ix_test_attempts_student_created ON test_attempts(student_id, created_at);
    """)

    # 8. Add foreign keys
    op.execute("""
        ALTER TABLE test_attempts
        ADD CONSTRAINT test_attempts_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

        ALTER TABLE test_attempts
        ADD CONSTRAINT test_attempts_test_id_fkey
        FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE CASCADE;

        ALTER TABLE test_attempts
        ADD CONSTRAINT test_attempts_school_id_fkey
        FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;
    """)

    # 9. Recreate FK from test_attempt_answers
    op.execute("""
        ALTER TABLE test_attempt_answers
        ADD CONSTRAINT test_attempt_answers_attempt_id_fkey
        FOREIGN KEY (attempt_id) REFERENCES test_attempts(id) ON DELETE CASCADE;
    """)

    # 10. Enable RLS
    op.execute("""
        ALTER TABLE test_attempts ENABLE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation_policy ON test_attempts
        FOR ALL USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );
    """)
