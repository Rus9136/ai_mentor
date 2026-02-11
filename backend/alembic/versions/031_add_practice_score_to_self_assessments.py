"""Add practice_score and time_spent to paragraph_self_assessments

Revision ID: 031_practice_score
Revises: 030_self_assessments
Create Date: 2026-02-11
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '031_practice_score'
down_revision = '030_self_assessments'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'paragraph_self_assessments',
        sa.Column('practice_score', sa.Float(), nullable=True),
    )
    op.add_column(
        'paragraph_self_assessments',
        sa.Column('time_spent', sa.Integer(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('paragraph_self_assessments', 'time_spent')
    op.drop_column('paragraph_self_assessments', 'practice_score')
