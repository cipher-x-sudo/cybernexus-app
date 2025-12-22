
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '006_notifications_timestamp'
down_revision = '005_notifications'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if notifications table exists and if timestamp column is missing
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'notifications' in tables:
        columns = [col['name'] for col in inspector.get_columns('notifications')]
        
        # Add timestamp column if it doesn't exist
        if 'timestamp' not in columns:
            op.add_column('notifications', sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False))
            
            # Create index for timestamp if it doesn't exist
            indexes = [idx['name'] for idx in inspector.get_indexes('notifications')]
            if 'ix_notifications_timestamp' not in indexes:
                op.create_index('ix_notifications_timestamp', 'notifications', ['timestamp'])


def downgrade() -> None:
    # Only drop if exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'notifications' in tables:
        columns = [col['name'] for col in inspector.get_columns('notifications')]
        if 'timestamp' in columns:
            # Drop index first
            indexes = [idx['name'] for idx in inspector.get_indexes('notifications')]
            if 'ix_notifications_timestamp' in indexes:
                op.drop_index('ix_notifications_timestamp', table_name='notifications')
            op.drop_column('notifications', 'timestamp')

