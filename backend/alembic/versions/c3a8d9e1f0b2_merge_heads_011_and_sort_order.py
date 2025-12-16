"""merge heads: 011 (paragraph key_terms/questions) + sort_order rename

This is a pure Alembic merge revision to make the migration graph single-head.

Revision ID: c3a8d9e1f0b2
Revises: b7e1f9a3c2d4, 011
Create Date: 2025-12-12
"""

from typing import Sequence, Union


# revision identifiers, used by Alembic.
revision: str = "c3a8d9e1f0b2"
down_revision: Union[tuple[str, str], str, None] = ("b7e1f9a3c2d4", "011")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Merge revision: no schema changes
    pass


def downgrade() -> None:
    # Merge revision: no schema changes
    pass


