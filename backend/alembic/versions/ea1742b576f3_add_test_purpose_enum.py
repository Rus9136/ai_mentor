"""add_test_purpose_enum

Adds TestPurpose enum to support different test types in the learning workflow.

Test purposes:
- diagnostic: Pre-chapter assessment to determine starting point
- formative: Post-paragraph tests for ongoing assessment (default)
- summative: Post-chapter comprehensive tests (highest weight for mastery)
- practice: Self-study tests that don't affect mastery level

Revision ID: ea1742b576f3
Revises: 401bffeccd70
Create Date: 2025-11-07 08:41:00.940734

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ea1742b576f3'
down_revision: Union[str, None] = '401bffeccd70'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create TestPurpose enum type
    op.execute("""
        CREATE TYPE testpurpose AS ENUM (
            'diagnostic',
            'formative',
            'summative',
            'practice'
        )
    """)

    # Add test_purpose column to tests table with default 'formative'
    op.add_column(
        'tests',
        sa.Column(
            'test_purpose',
            sa.Enum('diagnostic', 'formative', 'summative', 'practice', name='testpurpose'),
            nullable=False,
            server_default='formative'
        )
    )

    # Create index on (test_purpose, is_active) for efficient filtering
    op.create_index(
        'ix_tests_purpose_active',
        'tests',
        ['test_purpose', 'is_active']
    )


def downgrade() -> None:
    # Drop index
    op.drop_index('ix_tests_purpose_active', table_name='tests')

    # Drop test_purpose column
    op.drop_column('tests', 'test_purpose')

    # Drop testpurpose enum type
    op.execute('DROP TYPE testpurpose')
