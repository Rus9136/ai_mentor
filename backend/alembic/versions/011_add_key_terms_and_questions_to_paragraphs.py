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


# revision identifiers, used by Alembic.
revision: str = '011'
down_revision: Union[str, None] = '010'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # NOTE: make migration idempotent to support environments where columns
    # might have been added manually.
    op.execute("ALTER TABLE paragraphs ADD COLUMN IF NOT EXISTS key_terms JSON;")
    op.execute("ALTER TABLE paragraphs ADD COLUMN IF NOT EXISTS questions JSON;")


def downgrade() -> None:
    # NOTE: make migration idempotent
    op.execute("ALTER TABLE paragraphs DROP COLUMN IF EXISTS questions;")
    op.execute("ALTER TABLE paragraphs DROP COLUMN IF EXISTS key_terms;")
