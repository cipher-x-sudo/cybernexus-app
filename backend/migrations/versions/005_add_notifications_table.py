
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '005_notifications'
down_revision = '004_metadata_rename'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if notifications table already exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'notifications' not in tables:
        op.create_table(
            'notifications',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('channel', sa.String(length=50), nullable=False),
            sa.Column('priority', sa.String(length=20), nullable=False),
            sa.Column('title', sa.String(length=500), nullable=False),
            sa.Column('message', sa.Text(), nullable=False),
            sa.Column('severity', sa.String(length=20), nullable=False),
            sa.Column('read', sa.Boolean(), nullable=False, server_default='false'),
            sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('meta_data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_notifications_user_id', 'notifications', ['user_id'])
        op.create_index('ix_notifications_channel', 'notifications', ['channel'])
        op.create_index('ix_notifications_priority', 'notifications', ['priority'])
        op.create_index('ix_notifications_read', 'notifications', ['read'])
        op.create_index('ix_notifications_timestamp', 'notifications', ['timestamp'])
        op.create_index('ix_notifications_created_at', 'notifications', ['created_at'])
        op.create_index('idx_notification_user_read', 'notifications', ['user_id', 'read'])
        op.create_index('idx_notification_user_created', 'notifications', ['user_id', 'created_at'])
        op.create_index('idx_notification_channel', 'notifications', ['channel', 'created_at'])


def downgrade() -> None:
    # Only drop if exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'notifications' in tables:
        # Drop indexes first
        indexes = [idx['name'] for idx in inspector.get_indexes('notifications')]
        for idx_name in indexes:
            try:
                op.drop_index(idx_name, table_name='notifications')
            except Exception:
                pass
        
        op.drop_table('notifications')

