
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect


revision = '004_metadata_rename'
down_revision = '003_onboarding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    
    conn = op.get_bind()
    inspector = inspect(conn)
    

    if 'entities' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('entities')]
        if 'metadata' in columns and 'meta_data' not in columns:
            op.alter_column('entities', 'metadata', new_column_name='meta_data')
    

    if 'graph_edges' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('graph_edges')]
        if 'metadata' in columns and 'meta_data' not in columns:
            op.alter_column('graph_edges', 'metadata', new_column_name='meta_data')
    

    if 'user_activity_logs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('user_activity_logs')]
        if 'metadata' in columns and 'meta_data' not in columns:
            op.alter_column('user_activity_logs', 'metadata', new_column_name='meta_data')


def downgrade() -> None:
    
    conn = op.get_bind()
    inspector = inspect(conn)
    

    if 'entities' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('entities')]
        if 'meta_data' in columns and 'metadata' not in columns:
            op.alter_column('entities', 'meta_data', new_column_name='metadata')
    

    if 'graph_edges' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('graph_edges')]
        if 'meta_data' in columns and 'metadata' not in columns:
            op.alter_column('graph_edges', 'meta_data', new_column_name='metadata')
    

    if 'user_activity_logs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('user_activity_logs')]
        if 'meta_data' in columns and 'metadata' not in columns:
            op.alter_column('user_activity_logs', 'meta_data', new_column_name='metadata')





