"""Fix assignment_tests table - add soft delete fields

Revision ID: 007
Revises: 006
Create Date: 2025-10-29

This migration fixes an error in migration 001 where assignment_tests table
was created without soft delete fields (created_at, updated_at, deleted_at, is_deleted)
despite the model inheriting from SoftDeleteModel.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP

# revision identifiers, used by Alembic.
revision: str = '007'
down_revision: Union[str, None] = '006'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add soft delete and timestamp fields to assignment_tests
    op.add_column('assignment_tests', sa.Column('created_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('assignment_tests', sa.Column('updated_at', TIMESTAMP(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('assignment_tests', sa.Column('deleted_at', TIMESTAMP(timezone=True), nullable=True))
    op.add_column('assignment_tests', sa.Column('is_deleted', sa.Boolean(), nullable=False, server_default='false'))

    # Add index for soft delete filtering
    op.create_index(
        'ix_assignment_tests_is_deleted_created',
        'assignment_tests',
        ['is_deleted', 'created_at'],
        unique=False
    )


def downgrade() -> None:
    # Remove soft delete index
    op.drop_index('ix_assignment_tests_is_deleted_created', table_name='assignment_tests')

    # Remove soft delete and timestamp fields
    op.drop_column('assignment_tests', 'is_deleted')
    op.drop_column('assignment_tests', 'deleted_at')
    op.drop_column('assignment_tests', 'updated_at')
    op.drop_column('assignment_tests', 'created_at')
