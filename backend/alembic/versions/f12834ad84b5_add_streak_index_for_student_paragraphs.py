"""add_streak_index_for_student_paragraphs

Revision ID: f12834ad84b5
Revises: 020
Create Date: 2025-12-23 12:35:48.067563

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from alembic.operations import Operations


# revision identifiers, used by Alembic.
revision: str = 'f12834ad84b5'
down_revision: Union[str, None] = '020'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Add partial index for efficient streak calculation.

    This index optimizes the streak calculation query which:
    - Filters by student_id and school_id
    - Orders by last_accessed_at DESC
    - Only considers rows where last_accessed_at IS NOT NULL

    Note: CONCURRENTLY requires autocommit, so we use raw connection.
    """
    # Get raw connection for autocommit mode (required for CONCURRENTLY)
    connection = op.get_bind()
    # Set autocommit for this operation
    connection.execution_options(isolation_level="AUTOCOMMIT")
    connection.execute(sa.text("""
        CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_student_paragraph_streak
        ON student_paragraphs (student_id, school_id, last_accessed_at DESC)
        WHERE last_accessed_at IS NOT NULL
    """))


def downgrade() -> None:
    connection = op.get_bind()
    connection.execution_options(isolation_level="AUTOCOMMIT")
    connection.execute(sa.text("DROP INDEX CONCURRENTLY IF EXISTS idx_student_paragraph_streak"))
