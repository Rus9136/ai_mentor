"""Add attachments field to homework and homework_tasks tables

Revision ID: 028_add_homework_attachments
Revises: 027_fix_join_requests_rls
Create Date: 2025-01-22

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '028_add_homework_attachments'
down_revision = '027_fix_join_requests_rls'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add attachments column to homework table
    # Format: [{"url": "/uploads/...", "name": "file.pdf", "type": "pdf", "size": 1024}]
    op.add_column(
        'homework',
        sa.Column('attachments', JSONB, nullable=True)
    )

    # Add attachments column to homework_tasks table
    # Format: [{"url": "/uploads/...", "name": "diagram.png", "type": "image", "size": 2048}]
    op.add_column(
        'homework_tasks',
        sa.Column('attachments', JSONB, nullable=True)
    )


def downgrade() -> None:
    op.drop_column('homework_tasks', 'attachments')
    op.drop_column('homework', 'attachments')
