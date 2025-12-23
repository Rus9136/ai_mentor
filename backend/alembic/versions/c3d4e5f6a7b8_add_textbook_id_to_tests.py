"""Add textbook_id to tests table.

Adds textbook_id column to tests table for direct textbook binding.
Backfills existing tests by deriving textbook_id from chapter_id.

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2025-12-22
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add textbook_id column to tests table."""
    # Add textbook_id column (nullable initially for existing data)
    op.add_column(
        'tests',
        sa.Column('textbook_id', sa.Integer(), nullable=True)
    )

    # Add foreign key constraint
    op.create_foreign_key(
        'fk_tests_textbook_id',
        'tests', 'textbooks',
        ['textbook_id'], ['id'],
        ondelete='CASCADE'
    )

    # Add index for performance
    op.create_index('ix_tests_textbook_id', 'tests', ['textbook_id'])

    # Backfill: derive textbook_id from chapter_id for existing tests
    op.execute("""
        UPDATE tests t
        SET textbook_id = c.textbook_id
        FROM chapters c
        WHERE t.chapter_id = c.id AND t.textbook_id IS NULL
    """)


def downgrade() -> None:
    """Remove textbook_id column from tests table."""
    op.drop_index('ix_tests_textbook_id', table_name='tests')
    op.drop_constraint('fk_tests_textbook_id', 'tests', type_='foreignkey')
    op.drop_column('tests', 'textbook_id')
