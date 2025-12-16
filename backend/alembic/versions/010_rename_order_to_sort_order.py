"""rename order to sort_order (idempotent)

NOTE: This file originally existed in the repo with a duplicate Alembic revision id ('010'),
which conflicted with `010_add_textbook_versioning.py`. Duplicate revision ids break the
Alembic graph.

For a safe forward-only fix, we keep the file path for audit/history, but we correct the
revision id and place it after the current mainline head. The rename itself is idempotent:
it will only run if the source column exists and the target column does not.

Revision ID: b7e1f9a3c2d4
Revises: d6cfba8cd6fd
Create Date: 2025-12-12
"""

from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7e1f9a3c2d4"
down_revision: Union[str, None] = "d6cfba8cd6fd"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename questions.order -> questions.sort_order (only if needed)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'questions'
                  AND column_name = 'order'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'questions'
                  AND column_name = 'sort_order'
            )
            THEN
                EXECUTE 'ALTER TABLE questions RENAME COLUMN "order" TO sort_order';
            END IF;
        END $$;
        """
    )

    # Rename question_options.order -> question_options.sort_order (only if needed)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'question_options'
                  AND column_name = 'order'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'question_options'
                  AND column_name = 'sort_order'
            )
            THEN
                EXECUTE 'ALTER TABLE question_options RENAME COLUMN "order" TO sort_order';
            END IF;
        END $$;
        """
    )


def downgrade() -> None:
    # Revert questions.sort_order -> questions.order (only if needed)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'questions'
                  AND column_name = 'sort_order'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'questions'
                  AND column_name = 'order'
            )
            THEN
                EXECUTE 'ALTER TABLE questions RENAME COLUMN sort_order TO "order"';
            END IF;
        END $$;
        """
    )

    # Revert question_options.sort_order -> question_options.order (only if needed)
    op.execute(
        """
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'question_options'
                  AND column_name = 'sort_order'
            )
            AND NOT EXISTS (
                SELECT 1
                FROM information_schema.columns
                WHERE table_schema = 'public'
                  AND table_name = 'question_options'
                  AND column_name = 'order'
            )
            THEN
                EXECUTE 'ALTER TABLE question_options RENAME COLUMN sort_order TO "order"';
            END IF;
        END $$;
        """
    )


