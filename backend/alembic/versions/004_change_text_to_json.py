"""Change TEXT to JSON for selected_option_ids and sync data

Revision ID: 004
Revises: 003
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Change test_attempt_answers.selected_option_ids from TEXT to JSON
    # Using CASE to handle NULL values and convert text to JSON
    op.execute("""
        ALTER TABLE test_attempt_answers
        ALTER COLUMN selected_option_ids TYPE JSON
        USING CASE
            WHEN selected_option_ids IS NULL THEN NULL
            WHEN selected_option_ids = '' THEN NULL
            ELSE selected_option_ids::json
        END
    """)

    # Change sync_queue.data from TEXT to JSON
    # This field is NOT NULL, so we only need to handle the conversion
    op.execute("""
        ALTER TABLE sync_queue
        ALTER COLUMN data TYPE JSON
        USING data::json
    """)


def downgrade() -> None:
    # Revert test_attempt_answers.selected_option_ids from JSON to TEXT
    op.execute("""
        ALTER TABLE test_attempt_answers
        ALTER COLUMN selected_option_ids TYPE TEXT
        USING CASE
            WHEN selected_option_ids IS NULL THEN NULL
            ELSE selected_option_ids::text
        END
    """)

    # Revert sync_queue.data from JSON to TEXT
    op.execute("""
        ALTER TABLE sync_queue
        ALTER COLUMN data TYPE TEXT
        USING data::text
    """)
