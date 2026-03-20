"""Add language column to school_classes table.

Revision ID: 071_school_class_language
Revises: 070_textbook_language
"""
from alembic import op
import sqlalchemy as sa

revision = '071_school_class_language'
down_revision = '070_textbook_language'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('school_classes', sa.Column('language', sa.String(2), nullable=False, server_default='kk'))
    op.execute("""
        ALTER TABLE school_classes
        ADD CONSTRAINT chk_school_class_language CHECK (language IN ('kk', 'ru'))
    """)


def downgrade() -> None:
    op.execute("ALTER TABLE school_classes DROP CONSTRAINT IF EXISTS chk_school_class_language")
    op.drop_column('school_classes', 'language')
