"""Add learning and lesson objectives

Revision ID: 002
Revises: 001
Create Date: 2025-10-29

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add learning_objective column to chapters table
    op.add_column('chapters', sa.Column('learning_objective', sa.Text(), nullable=True))

    # Add lesson_objective column to paragraphs table
    op.add_column('paragraphs', sa.Column('lesson_objective', sa.Text(), nullable=True))


def downgrade() -> None:
    # Remove lesson_objective column from paragraphs table
    op.drop_column('paragraphs', 'lesson_objective')

    # Remove learning_objective column from chapters table
    op.drop_column('chapters', 'learning_objective')
