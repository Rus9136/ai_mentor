"""Add challenge_id to chat_sessions for coding AI mentor.

Revision ID: 072_coding_chat
Revises: 071_school_class_language
"""
from alembic import op
import sqlalchemy as sa

revision = '072_coding_chat'
down_revision = '071_school_class_language'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'chat_sessions',
        sa.Column('challenge_id', sa.Integer(),
                  sa.ForeignKey('coding_challenges.id', ondelete='SET NULL'),
                  nullable=True)
    )
    op.create_index(
        'idx_chat_sessions_challenge',
        'chat_sessions',
        ['challenge_id'],
        postgresql_where=sa.text('challenge_id IS NOT NULL')
    )


def downgrade() -> None:
    op.drop_index('idx_chat_sessions_challenge', table_name='chat_sessions')
    op.drop_column('chat_sessions', 'challenge_id')
