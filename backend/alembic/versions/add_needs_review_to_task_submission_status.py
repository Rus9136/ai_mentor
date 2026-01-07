"""Add needs_review to task_submission_status_enum

Revision ID: add_needs_review_enum
Revises: f12834ad84b5
Create Date: 2026-01-07 08:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'add_needs_review_enum'
down_revision: Union[str, None] = 'f12834ad84b5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add 'needs_review' value to task_submission_status_enum
    # This is already applied directly to the database, but we document it here
    # Note: PostgreSQL ALTER TYPE ADD VALUE cannot be inside a transaction
    # So this is a no-op migration for documentation purposes
    # The value was added with: ALTER TYPE task_submission_status_enum ADD VALUE 'needs_review' AFTER 'submitted';
    pass


def downgrade() -> None:
    # PostgreSQL doesn't support removing enum values directly
    # Would require recreating the enum type and all columns using it
    pass
