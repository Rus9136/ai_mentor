"""
Add board_state JSONB column to quiz_sessions for Factile game mode.

Revision ID: 074_quiz_factile
Revises: 073_teacher_subjects
"""

revision = '074_quiz_factile'
down_revision = '073_teacher_subjects'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


def upgrade():
    # Add board_state column for Factile mode runtime state
    # (categories grid, cell statuses, current turn, active cell)
    op.add_column('quiz_sessions', sa.Column('board_state', JSONB, nullable=True))


def downgrade():
    op.drop_column('quiz_sessions', 'board_state')
