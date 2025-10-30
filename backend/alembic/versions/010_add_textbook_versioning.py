"""Add versioning support to textbooks

Revision ID: 010
Revises: 009
Create Date: 2025-10-30

This migration adds version tracking to textbooks to support:
- Version management for global textbooks
- Tracking source version when customizing (forking) a global textbook
- Future content update synchronization
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
    # Add version column - tracks current version of textbook
    op.add_column(
        'textbooks',
        sa.Column('version', sa.Integer(), nullable=False, server_default='1')
    )

    # Add source_version column - tracks version of global textbook at fork time
    op.add_column(
        'textbooks',
        sa.Column('source_version', sa.Integer(), nullable=True)
    )

    # Remove server_default after creation (we want default only for new rows)
    op.alter_column('textbooks', 'version', server_default=None)


def downgrade() -> None:
    # Remove versioning columns
    op.drop_column('textbooks', 'source_version')
    op.drop_column('textbooks', 'version')
