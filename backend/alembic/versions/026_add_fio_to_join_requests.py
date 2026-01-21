"""Add FIO fields to student join requests

Revision ID: 026_add_fio_to_join_requests
Revises: 025_add_student_join_requests
Create Date: 2026-01-21

This migration adds first_name, last_name, middle_name fields to student_join_requests
table to store the student's FIO as provided during the join request.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '026_add_fio_to_join_requests'
down_revision: Union[str, None] = '025_add_student_join_requests'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add FIO columns to student_join_requests
    op.add_column(
        'student_join_requests',
        sa.Column('first_name', sa.String(100), nullable=True)
    )
    op.add_column(
        'student_join_requests',
        sa.Column('last_name', sa.String(100), nullable=True)
    )
    op.add_column(
        'student_join_requests',
        sa.Column('middle_name', sa.String(100), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('student_join_requests', 'middle_name')
    op.drop_column('student_join_requests', 'last_name')
    op.drop_column('student_join_requests', 'first_name')
