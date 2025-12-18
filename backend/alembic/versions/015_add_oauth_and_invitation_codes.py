"""Add OAuth fields to users and invitation_codes table

This migration adds:
1. OAuth fields to users table (auth_provider, google_id, avatar_url)
2. Makes password_hash nullable for OAuth users
3. Creates invitation_codes table for student registration
4. Creates invitation_code_uses table for audit trail
5. RLS policies for invitation_codes

Revision ID: 015
Revises: 014
Create Date: 2025-12-18
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "015"
down_revision: Union[str, None] = "014"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create auth_provider enum type
    auth_provider_enum = postgresql.ENUM('local', 'google', name='authprovider', create_type=False)
    auth_provider_enum.create(op.get_bind(), checkfirst=True)

    # Add OAuth columns to users table
    op.add_column('users', sa.Column('auth_provider', sa.Enum('local', 'google', name='authprovider'),
                                      nullable=False, server_default='local'))
    op.add_column('users', sa.Column('google_id', sa.String(255), nullable=True))
    op.add_column('users', sa.Column('avatar_url', sa.String(500), nullable=True))

    # Make password_hash nullable (for OAuth users who don't have passwords)
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=True)

    # Create index on google_id
    op.create_index('ix_users_google_id', 'users', ['google_id'], unique=True)

    # Create invitation_codes table
    op.create_table(
        'invitation_codes',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=True),
        sa.Column('grade_level', sa.Integer(), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('max_uses', sa.Integer(), nullable=True),
        sa.Column('uses_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_by', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['school_classes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ondelete='CASCADE'),
        sa.CheckConstraint('grade_level >= 1 AND grade_level <= 11', name='check_grade_level'),
        sa.CheckConstraint('uses_count >= 0', name='check_uses_count'),
    )

    # Create indexes for invitation_codes
    op.create_index('ix_invitation_codes_code', 'invitation_codes', ['code'], unique=True)
    op.create_index('ix_invitation_codes_school_id', 'invitation_codes', ['school_id'])
    op.create_index('ix_invitation_codes_is_active', 'invitation_codes', ['is_active'])

    # Create invitation_code_uses table (audit trail)
    op.create_table(
        'invitation_code_uses',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('invitation_code_id', sa.Integer(), nullable=False),
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  onupdate=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['invitation_code_id'], ['invitation_codes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
    )

    # Create indexes for invitation_code_uses
    op.create_index('ix_invitation_code_uses_code_id', 'invitation_code_uses', ['invitation_code_id'])
    op.create_index('ix_invitation_code_uses_student_id', 'invitation_code_uses', ['student_id'])

    # Enable RLS on invitation_codes
    op.execute("ALTER TABLE invitation_codes ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE invitation_codes FORCE ROW LEVEL SECURITY")

    # RLS policies for invitation_codes
    # School admins can only see/manage codes from their school
    op.execute("""
        CREATE POLICY invitation_codes_select_policy ON invitation_codes
        FOR SELECT
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        )
    """)

    op.execute("""
        CREATE POLICY invitation_codes_insert_policy ON invitation_codes
        FOR INSERT
        WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        )
    """)

    op.execute("""
        CREATE POLICY invitation_codes_update_policy ON invitation_codes
        FOR UPDATE
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        )
    """)

    op.execute("""
        CREATE POLICY invitation_codes_delete_policy ON invitation_codes
        FOR DELETE
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
        )
    """)

    # Enable RLS on invitation_code_uses
    op.execute("ALTER TABLE invitation_code_uses ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE invitation_code_uses FORCE ROW LEVEL SECURITY")

    # RLS policies for invitation_code_uses (same as invitation_codes, based on parent school)
    op.execute("""
        CREATE POLICY invitation_code_uses_select_policy ON invitation_code_uses
        FOR SELECT
        USING (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR invitation_code_id IN (
                SELECT id FROM invitation_codes
                WHERE school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
            )
        )
    """)

    op.execute("""
        CREATE POLICY invitation_code_uses_insert_policy ON invitation_code_uses
        FOR INSERT
        WITH CHECK (
            COALESCE(current_setting('app.is_super_admin', true), 'false')::boolean = true
            OR invitation_code_id IN (
                SELECT id FROM invitation_codes
                WHERE school_id = COALESCE(NULLIF(current_setting('app.current_tenant_id', true), ''), '0')::integer
            )
        )
    """)

    # Grant permissions to app user
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON invitation_codes TO ai_mentor_app")
    op.execute("GRANT SELECT, INSERT ON invitation_code_uses TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE invitation_codes_id_seq TO ai_mentor_app")
    op.execute("GRANT USAGE, SELECT ON SEQUENCE invitation_code_uses_id_seq TO ai_mentor_app")


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS invitation_code_uses_insert_policy ON invitation_code_uses")
    op.execute("DROP POLICY IF EXISTS invitation_code_uses_select_policy ON invitation_code_uses")
    op.execute("DROP POLICY IF EXISTS invitation_codes_delete_policy ON invitation_codes")
    op.execute("DROP POLICY IF EXISTS invitation_codes_update_policy ON invitation_codes")
    op.execute("DROP POLICY IF EXISTS invitation_codes_insert_policy ON invitation_codes")
    op.execute("DROP POLICY IF EXISTS invitation_codes_select_policy ON invitation_codes")

    # Drop tables
    op.drop_table('invitation_code_uses')
    op.drop_table('invitation_codes')

    # Remove OAuth columns from users
    op.drop_index('ix_users_google_id', table_name='users')
    op.drop_column('users', 'avatar_url')
    op.drop_column('users', 'google_id')
    op.drop_column('users', 'auth_provider')

    # Make password_hash NOT NULL again
    op.alter_column('users', 'password_hash',
                    existing_type=sa.String(255),
                    nullable=False)

    # Drop enum type
    op.execute("DROP TYPE IF EXISTS authprovider")
