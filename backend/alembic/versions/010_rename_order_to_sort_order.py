"""rename order to sort_order

Revision ID: 010
Revises: 009
Create Date: 2025-11-08 10:04:20

Rename the 'order' column to 'sort_order' in questions and question_options tables.
The 'order' is a SQL reserved keyword and causes issues with asyncpg parameter binding.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '010'
down_revision: Union[str, None] = '009'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Rename order column in questions table
    op.alter_column('questions', 'order', new_column_name='sort_order')

    # Rename order column in question_options table
    op.alter_column('question_options', 'order', new_column_name='sort_order')


def downgrade() -> None:
    # Revert sort_order back to order in questions table
    op.alter_column('questions', 'sort_order', new_column_name='order')

    # Revert sort_order back to order in question_options table
    op.alter_column('question_options', 'sort_order', new_column_name='order')
