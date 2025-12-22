
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '007_jobs'
down_revision = '006_notifications_timestamp'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if jobs table already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'jobs' not in tables:
        op.create_table(
            'jobs',
            sa.Column('id', sa.String(length=255), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('capability', sa.String(length=50), nullable=False),
            sa.Column('target', sa.String(length=500), nullable=False),
            sa.Column('status', sa.String(length=20), nullable=False),
            sa.Column('priority', sa.Integer(), nullable=False, server_default='2'),
            sa.Column('progress', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('error', sa.Text(), nullable=True),
            sa.Column('execution_logs', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_jobs_user_id', 'jobs', ['user_id'])
        op.create_index('ix_jobs_capability', 'jobs', ['capability'])
        op.create_index('ix_jobs_status', 'jobs', ['status'])
        op.create_index('ix_jobs_created_at', 'jobs', ['created_at'])
        op.create_index('idx_job_user_status', 'jobs', ['user_id', 'status'])
        op.create_index('idx_job_user_capability', 'jobs', ['user_id', 'capability'])
        op.create_index('idx_job_user_created', 'jobs', ['user_id', 'created_at'])
        op.create_index('idx_job_status_created', 'jobs', ['status', 'created_at'])


def downgrade() -> None:
    # Only drop if exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'jobs' in tables:
        # Drop indexes first
        indexes = [idx['name'] for idx in inspector.get_indexes('jobs')]
        for idx_name in indexes:
            try:
                op.drop_index(idx_name, table_name='jobs')
            except Exception:
                pass
        
        op.drop_table('jobs')

