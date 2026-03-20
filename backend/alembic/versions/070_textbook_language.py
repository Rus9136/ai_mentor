"""Add language column to textbooks table.

Revision ID: 070_textbook_language
Revises: 069_coding_gamification
"""
from alembic import op
import sqlalchemy as sa

revision = '070_textbook_language'
down_revision = '069_coding_gamification'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add language column: 'kk' (Kazakh) or 'ru' (Russian)
    op.add_column('textbooks', sa.Column('language', sa.String(2), nullable=True))

    # Set default based on existing textbook titles (heuristic)
    op.execute("""
        UPDATE textbooks SET language = 'ru'
        WHERE title ~* '(класс|часть|алгебра 7)'
        AND language IS NULL
    """)
    op.execute("""
        UPDATE textbooks SET language = 'kk'
        WHERE language IS NULL
    """)

    # Make NOT NULL with default
    op.alter_column('textbooks', 'language', nullable=False, server_default='kk')

    # Add check constraint
    op.execute("""
        ALTER TABLE textbooks
        ADD CONSTRAINT chk_textbook_language CHECK (language IN ('kk', 'ru'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE textbooks DROP CONSTRAINT IF EXISTS chk_textbook_language")
    op.drop_column('textbooks', 'language')
