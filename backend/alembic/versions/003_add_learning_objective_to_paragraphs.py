"""Add learning_objective to paragraphs

Revision ID: 003
Revises: 002
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add learning_objective column to paragraphs table
    op.add_column('paragraphs', sa.Column('learning_objective', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove learning_objective column from paragraphs table
    op.drop_column('paragraphs', 'learning_objective')
