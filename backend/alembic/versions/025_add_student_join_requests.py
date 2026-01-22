"""Add student join requests table

Revision ID: 025_add_student_join_requests
Revises: b7d8e9f0a1b2
Create Date: 2025-01-21

This migration adds the student_join_requests table for class enrollment
approval workflow. Students request to join a class, and teachers approve/reject.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = '025_add_student_join_requests'
down_revision: Union[str, None] = 'b7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create ENUM type
    join_request_status_enum = postgresql.ENUM(
        'pending', 'approved', 'rejected',
        name='join_request_status_enum',
        create_type=False
    )
    join_request_status_enum.create(op.get_bind(), checkfirst=True)

    # Create table
    op.create_table(
        'student_join_requests',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), onupdate=sa.func.now(), nullable=False),

        # Foreign keys
        sa.Column('student_id', sa.Integer(), nullable=False),
        sa.Column('class_id', sa.Integer(), nullable=False),
        sa.Column('school_id', sa.Integer(), nullable=False),
        sa.Column('invitation_code_id', sa.Integer(), nullable=True),

        # Status
        sa.Column('status', postgresql.ENUM('pending', 'approved', 'rejected', name='join_request_status_enum', create_type=False), nullable=False, server_default='pending'),

        # Review info
        sa.Column('reviewed_by', sa.Integer(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('rejection_reason', sa.Text(), nullable=True),

        # Constraints
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['school_classes.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['school_id'], ['schools.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['invitation_code_id'], ['invitation_codes.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['reviewed_by'], ['users.id'], ondelete='SET NULL'),

        # Unique constraint for one request per student-class combination
        sa.UniqueConstraint('student_id', 'class_id', name='uq_student_class_join_request'),
    )

    # Create indexes
    op.create_index('idx_join_request_student', 'student_join_requests', ['student_id'])
    op.create_index('idx_join_request_class', 'student_join_requests', ['class_id'])
    op.create_index('idx_join_request_school', 'student_join_requests', ['school_id'])
    op.create_index('idx_join_request_status', 'student_join_requests', ['status'])
    op.create_index('idx_join_request_school_status', 'student_join_requests', ['school_id', 'status'])
    op.create_index('idx_join_request_class_status', 'student_join_requests', ['class_id', 'status'])
    op.create_index('idx_join_request_invitation', 'student_join_requests', ['invitation_code_id'])

    # Add RLS policy for school isolation
    op.execute("""
        ALTER TABLE student_join_requests ENABLE ROW LEVEL SECURITY;

        CREATE POLICY student_join_requests_tenant_isolation ON student_join_requests
            USING (
                COALESCE(current_setting('app.current_tenant_id', true), '0')::integer = 0
                OR school_id = COALESCE(current_setting('app.current_tenant_id', true), '0')::integer
            );
    """)


def downgrade() -> None:
    # Drop RLS policy
    op.execute("DROP POLICY IF EXISTS student_join_requests_tenant_isolation ON student_join_requests;")
    op.execute("ALTER TABLE student_join_requests DISABLE ROW LEVEL SECURITY;")

    # Drop indexes
    op.drop_index('idx_join_request_invitation')
    op.drop_index('idx_join_request_class_status')
    op.drop_index('idx_join_request_school_status')
    op.drop_index('idx_join_request_status')
    op.drop_index('idx_join_request_school')
    op.drop_index('idx_join_request_class')
    op.drop_index('idx_join_request_student')

    # Drop table
    op.drop_table('student_join_requests')

    # Drop ENUM type
    op.execute("DROP TYPE IF EXISTS join_request_status_enum;")
