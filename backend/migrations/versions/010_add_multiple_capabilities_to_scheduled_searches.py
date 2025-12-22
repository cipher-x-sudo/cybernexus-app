
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '010_multiple_capabilities'
down_revision = '009_scheduled_searches'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'scheduled_searches' in tables:
        columns = [col['name'] for col in inspector.get_columns('scheduled_searches')]
        
        # Add new capabilities column (JSONB array)
        if 'capabilities' not in columns:
            op.add_column('scheduled_searches', 
                sa.Column('capabilities', postgresql.JSONB(astext_type=sa.Text()), nullable=True, server_default='[]')
            )
        
        # Migrate data: convert single capability to array
        # This will convert existing 'capability' values to ['capability'] in the new 'capabilities' column
        op.execute("""
            UPDATE scheduled_searches 
            SET capabilities = jsonb_build_array(capability::text)
            WHERE capabilities IS NULL OR capabilities = '[]'::jsonb
        """)
        
        # Make capabilities NOT NULL after migration
        op.alter_column('scheduled_searches', 'capabilities', nullable=False, server_default='[]')
        
        # Drop old capability column and its index
        indexes = [idx['name'] for idx in inspector.get_indexes('scheduled_searches')]
        if 'ix_scheduled_searches_capability' in indexes:
            try:
                op.drop_index('ix_scheduled_searches_capability', table_name='scheduled_searches')
            except Exception:
                pass
        if 'idx_scheduled_search_user_capability' in indexes:
            try:
                op.drop_index('idx_scheduled_search_user_capability', table_name='scheduled_searches')
            except Exception:
                pass
        
        if 'capability' in columns:
            op.drop_column('scheduled_searches', 'capability')


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'scheduled_searches' in tables:
        columns = [col['name'] for col in inspector.get_columns('scheduled_searches')]
        
        # Add back capability column
        if 'capability' not in columns:
            op.add_column('scheduled_searches',
                sa.Column('capability', sa.String(length=50), nullable=True)
            )
        
        # Migrate data: take first capability from array
        op.execute("""
            UPDATE scheduled_searches 
            SET capability = capabilities->>0
            WHERE capabilities IS NOT NULL AND jsonb_array_length(capabilities) > 0
        """)
        
        # Make capability NOT NULL
        op.alter_column('scheduled_searches', 'capability', nullable=False)
        
        # Recreate indexes
        op.create_index('ix_scheduled_searches_capability', 'scheduled_searches', ['capability'])
        op.create_index('idx_scheduled_search_user_capability', 'scheduled_searches', ['user_id', 'capability'])
        
        # Drop capabilities column
        if 'capabilities' in columns:
            op.drop_column('scheduled_searches', 'capabilities')


