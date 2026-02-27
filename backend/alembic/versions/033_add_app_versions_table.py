"""Add app_versions table for mobile client update checks

Revision ID: 033_app_versions
Revises: 032_exercises
Create Date: 2026-02-27
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '033_app_versions'
down_revision = '032_exercises'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create platform enum
    platform_enum = sa.Enum('android', 'ios', name='platform')
    platform_enum.create(op.get_bind(), checkfirst=True)

    # Create app_versions table
    op.create_table(
        'app_versions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('platform', platform_enum, nullable=False),
        sa.Column('latest_version', sa.String(20), nullable=False),
        sa.Column('min_version', sa.String(20), nullable=False),
        sa.Column('release_notes', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_app_versions_id', 'app_versions', ['id'])
    op.create_index('ix_app_versions_platform', 'app_versions', ['platform'])

    # Seed initial data
    op.execute(
        "INSERT INTO app_versions (platform, latest_version, min_version, is_active) "
        "VALUES ('android', '1.0.0', '1.0.0', true), "
        "       ('ios', '1.0.0', '1.0.0', true)"
    )


def downgrade() -> None:
    op.drop_index('ix_app_versions_platform', table_name='app_versions')
    op.drop_index('ix_app_versions_id', table_name='app_versions')
    op.drop_table('app_versions')

    # Drop enum
    sa.Enum(name='platform').drop(op.get_bind(), checkfirst=True)
