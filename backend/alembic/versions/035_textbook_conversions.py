"""Add textbook_conversions table for Mathpix PDF-to-MMD

Revision ID: 035_textbook_conversions
Revises: 034_grades
Create Date: 2026-03-04
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '035_textbook_conversions'
down_revision = '034_grades'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create conversion_status enum
    conversion_status_enum = sa.Enum(
        'PENDING', 'PROCESSING', 'COMPLETED', 'FAILED',
        name='conversion_status',
    )
    conversion_status_enum.create(op.get_bind(), checkfirst=True)

    # Create textbook_conversions table
    op.create_table(
        'textbook_conversions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('textbook_id', sa.Integer(), sa.ForeignKey('textbooks.id', ondelete='CASCADE'), nullable=False),
        sa.Column('status', conversion_status_enum, nullable=False, server_default='PENDING'),
        sa.Column('pdf_path', sa.String(500), nullable=False),
        sa.Column('mmd_path', sa.String(500), nullable=True),
        sa.Column('mathpix_pdf_id', sa.String(255), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )

    # Indexes
    op.create_index('ix_textbook_conversions_textbook_id', 'textbook_conversions', ['textbook_id'])
    op.create_index('ix_textbook_conversions_status', 'textbook_conversions', ['status'])

    # Grant permissions to app user
    op.execute("GRANT SELECT, INSERT, UPDATE ON textbook_conversions TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE textbook_conversions_id_seq TO ai_mentor_app")


def downgrade() -> None:
    op.drop_table('textbook_conversions')
    sa.Enum(name='conversion_status').drop(op.get_bind(), checkfirst=True)
