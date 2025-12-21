"""Rename metadata to meta_data (reserved in SQLAlchemy)

Revision ID: 004_metadata_rename
Revises: 003_onboarding
Create Date: 2024-01-01 00:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '004_metadata_rename'
down_revision = '003_onboarding'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Rename metadata columns to meta_data to avoid SQLAlchemy reserved name conflict."""
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Rename metadata column in entities table
    if 'entities' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('entities')]
        if 'metadata' in columns and 'meta_data' not in columns:
            op.alter_column('entities', 'metadata', new_column_name='meta_data')
    
    # Rename metadata column in graph_edges table
    if 'graph_edges' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('graph_edges')]
        if 'metadata' in columns and 'meta_data' not in columns:
            op.alter_column('graph_edges', 'metadata', new_column_name='meta_data')
    
    # Rename metadata column in user_activity_logs table
    if 'user_activity_logs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('user_activity_logs')]
        if 'metadata' in columns and 'meta_data' not in columns:
            op.alter_column('user_activity_logs', 'metadata', new_column_name='meta_data')


def downgrade() -> None:
    """Rename meta_data columns back to metadata."""
    conn = op.get_bind()
    inspector = inspect(conn)
    
    # Rename meta_data column back to metadata in entities table
    if 'entities' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('entities')]
        if 'meta_data' in columns and 'metadata' not in columns:
            op.alter_column('entities', 'meta_data', new_column_name='metadata')
    
    # Rename meta_data column back to metadata in graph_edges table
    if 'graph_edges' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('graph_edges')]
        if 'meta_data' in columns and 'metadata' not in columns:
            op.alter_column('graph_edges', 'meta_data', new_column_name='metadata')
    
    # Rename meta_data column back to metadata in user_activity_logs table
    if 'user_activity_logs' in inspector.get_table_names():
        columns = [col['name'] for col in inspector.get_columns('user_activity_logs')]
        if 'meta_data' in columns and 'metadata' not in columns:
            op.alter_column('user_activity_logs', 'meta_data', new_column_name='metadata')



