"""Partition learning_activities table by activity_timestamp (monthly)

Revision ID: a6f786ce22f9
Revises: 5d20a0c758f1
Create Date: 2026-01-07

This migration:
1. Converts learning_activities to a partitioned table (RANGE by activity_timestamp)
2. Creates monthly partitions from 2025-01 to 2027-12 (36 partitions)
3. Migrates existing data
4. Recreates indexes and RLS policies

Expected improvements:
- Faster queries with date filters for analytics
- Easier maintenance (VACUUM per partition)
- Simple archival (DROP old partitions)
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'a6f786ce22f9'
down_revision: Union[str, None] = '5d20a0c758f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Convert learning_activities to partitioned table."""

    # 1. Drop existing RLS policy first
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON learning_activities;
        DROP POLICY IF EXISTS tenant_insert_policy ON learning_activities;
    """)

    # 2. Rename old table
    op.execute("ALTER TABLE learning_activities RENAME TO learning_activities_old;")

    # 3. Drop old indexes (they reference old table)
    op.execute("""
        DROP INDEX IF EXISTS ix_learning_activities_session_id;
        DROP INDEX IF EXISTS ix_learning_activities_student_id;
        DROP INDEX IF EXISTS ix_learning_activities_school_id;
        DROP INDEX IF EXISTS ix_learning_activities_activity_type;
        DROP INDEX IF EXISTS ix_learning_activities_activity_timestamp;
    """)

    # 4. Create new partitioned table with same structure
    # Note: PRIMARY KEY must include the partition key (activity_timestamp)
    op.execute("""
        CREATE TABLE learning_activities (
            id SERIAL,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            activity_type VARCHAR(50) NOT NULL,
            activity_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            duration INTEGER,
            paragraph_id INTEGER,
            test_id INTEGER,
            activity_metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            PRIMARY KEY (id, activity_timestamp)
        ) PARTITION BY RANGE (activity_timestamp);
    """)

    # 5. Create monthly partitions (2025-01 to 2027-12)
    for year in [2025, 2026, 2027]:
        for month in range(1, 13):
            partition_name = f"learning_activities_{year}_{month:02d}"
            start_date = f"{year}-{month:02d}-01"

            if month == 12:
                end_date = f"{year + 1}-01-01"
            else:
                end_date = f"{year}-{month + 1:02d}-01"

            op.execute(f"""
                CREATE TABLE {partition_name}
                PARTITION OF learning_activities
                FOR VALUES FROM ('{start_date}') TO ('{end_date}');
            """)

    # 6. Create default partition for data outside defined ranges
    op.execute("""
        CREATE TABLE learning_activities_default
        PARTITION OF learning_activities DEFAULT;
    """)

    # 7. Migrate existing data
    op.execute("""
        INSERT INTO learning_activities (
            id, session_id, student_id, school_id, activity_type,
            activity_timestamp, duration, paragraph_id, test_id,
            activity_metadata, created_at, updated_at
        )
        SELECT
            id, session_id, student_id, school_id, activity_type,
            activity_timestamp, duration, paragraph_id, test_id,
            activity_metadata, created_at, updated_at
        FROM learning_activities_old;
    """)

    # 8. Reset sequence for id to max + 1
    op.execute("""
        SELECT setval('learning_activities_id_seq',
            COALESCE((SELECT MAX(id) FROM learning_activities), 0) + 1, false);
    """)

    # 9. Create indexes (will be created on each partition automatically)
    op.execute("""
        CREATE INDEX ix_learning_activities_session_id ON learning_activities(session_id);
        CREATE INDEX ix_learning_activities_student_id ON learning_activities(student_id);
        CREATE INDEX ix_learning_activities_school_id ON learning_activities(school_id);
        CREATE INDEX ix_learning_activities_activity_type ON learning_activities(activity_type);
        CREATE INDEX ix_learning_activities_activity_timestamp ON learning_activities(activity_timestamp);
        CREATE INDEX ix_learning_activities_student_timestamp ON learning_activities(student_id, activity_timestamp);
    """)

    # 10. Add foreign keys to parent table
    op.execute("""
        ALTER TABLE learning_activities
        ADD CONSTRAINT fk_learning_activities_session
        FOREIGN KEY (session_id) REFERENCES learning_sessions(id) ON DELETE CASCADE;

        ALTER TABLE learning_activities
        ADD CONSTRAINT fk_learning_activities_student
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

        ALTER TABLE learning_activities
        ADD CONSTRAINT fk_learning_activities_school
        FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

        ALTER TABLE learning_activities
        ADD CONSTRAINT fk_learning_activities_paragraph
        FOREIGN KEY (paragraph_id) REFERENCES paragraphs(id) ON DELETE SET NULL;

        ALTER TABLE learning_activities
        ADD CONSTRAINT fk_learning_activities_test
        FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE SET NULL;
    """)

    # 11. Enable RLS on partitioned table (inherits to partitions)
    op.execute("""
        ALTER TABLE learning_activities ENABLE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation_policy ON learning_activities
        FOR ALL USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );

        CREATE POLICY tenant_insert_policy ON learning_activities
        FOR INSERT WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );
    """)

    # 12. Drop old table
    op.execute("DROP TABLE learning_activities_old;")

    # 13. Add comment for documentation
    op.execute("""
        COMMENT ON TABLE learning_activities IS
        'Partitioned by activity_timestamp (monthly). Created 2026-01-07.
        Partitions: learning_activities_YYYY_MM for 2025-2027, learning_activities_default for others.
        Note: PRIMARY KEY is (id, activity_timestamp) for partition support.';
    """)


def downgrade() -> None:
    """Revert to non-partitioned table."""

    # 1. Drop RLS
    op.execute("""
        DROP POLICY IF EXISTS tenant_isolation_policy ON learning_activities;
        DROP POLICY IF EXISTS tenant_insert_policy ON learning_activities;
    """)

    # 2. Create non-partitioned table
    op.execute("""
        CREATE TABLE learning_activities_new (
            id SERIAL PRIMARY KEY,
            session_id INTEGER NOT NULL,
            student_id INTEGER NOT NULL,
            school_id INTEGER NOT NULL,
            activity_type VARCHAR(50) NOT NULL,
            activity_timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            duration INTEGER,
            paragraph_id INTEGER,
            test_id INTEGER,
            activity_metadata JSONB,
            created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
            updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
        );
    """)

    # 3. Copy data
    op.execute("""
        INSERT INTO learning_activities_new
        SELECT * FROM learning_activities;
    """)

    # 4. Drop partitioned table and all partitions
    op.execute("DROP TABLE learning_activities CASCADE;")

    # 5. Rename new table
    op.execute("ALTER TABLE learning_activities_new RENAME TO learning_activities;")

    # 6. Reset sequence
    op.execute("""
        SELECT setval('learning_activities_id_seq',
            COALESCE((SELECT MAX(id) FROM learning_activities), 0) + 1, false);
    """)

    # 7. Recreate indexes
    op.execute("""
        CREATE INDEX ix_learning_activities_session_id ON learning_activities(session_id);
        CREATE INDEX ix_learning_activities_student_id ON learning_activities(student_id);
        CREATE INDEX ix_learning_activities_school_id ON learning_activities(school_id);
        CREATE INDEX ix_learning_activities_activity_type ON learning_activities(activity_type);
        CREATE INDEX ix_learning_activities_activity_timestamp ON learning_activities(activity_timestamp);
    """)

    # 8. Add foreign keys
    op.execute("""
        ALTER TABLE learning_activities
        ADD CONSTRAINT learning_activities_session_id_fkey
        FOREIGN KEY (session_id) REFERENCES learning_sessions(id) ON DELETE CASCADE;

        ALTER TABLE learning_activities
        ADD CONSTRAINT learning_activities_student_id_fkey
        FOREIGN KEY (student_id) REFERENCES students(id) ON DELETE CASCADE;

        ALTER TABLE learning_activities
        ADD CONSTRAINT learning_activities_school_id_fkey
        FOREIGN KEY (school_id) REFERENCES schools(id) ON DELETE CASCADE;

        ALTER TABLE learning_activities
        ADD CONSTRAINT learning_activities_paragraph_id_fkey
        FOREIGN KEY (paragraph_id) REFERENCES paragraphs(id) ON DELETE SET NULL;

        ALTER TABLE learning_activities
        ADD CONSTRAINT learning_activities_test_id_fkey
        FOREIGN KEY (test_id) REFERENCES tests(id) ON DELETE SET NULL;
    """)

    # 9. Enable RLS
    op.execute("""
        ALTER TABLE learning_activities ENABLE ROW LEVEL SECURITY;

        CREATE POLICY tenant_isolation_policy ON learning_activities
        FOR ALL USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id::text = COALESCE(current_setting('app.current_tenant_id', true), '')
        );
    """)
