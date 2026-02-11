"""merge_024_and_029

Revision ID: c39cb6f883c7
Revises: 024, 029_add_apple_oauth
Create Date: 2026-02-11 04:20:46.692809

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c39cb6f883c7'
down_revision: Union[str, None] = ('024', '029_add_apple_oauth')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
