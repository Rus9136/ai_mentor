"""add key_terms and questions to paragraphs

Revision ID: 011
Revises: 010
Create Date: 2025-11-11

Add key_terms (JSON array of strings) and questions (JSON array of objects)
columns to the paragraphs table for enhanced content metadata.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add key_terms column - array of key terms as JSON
    op.add_column('paragraphs', sa.Column('key_terms', JSON, nullable=True))

    # Add questions column - array of questions (with order and text) as JSON
    op.add_column('paragraphs', sa.Column('questions', JSON, nullable=True))


def downgrade() -> None:
    # Remove questions column
    op.drop_column('paragraphs', 'questions')

    # Remove key_terms column
    op.drop_column('paragraphs', 'key_terms')
