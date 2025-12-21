"""Add automation_config to company_profiles

Revision ID: 011_automation_config
Revises: 010_multiple_capabilities
Create Date: 2024-01-22 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '011_automation_config'
down_revision = '010_multiple_capabilities'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'company_profiles' in tables:
        columns = [col['name'] for col in inspector.get_columns('company_profiles')]
        
        # Add automation_config column if it doesn't exist
        if 'automation_config' not in columns:
            op.add_column('company_profiles', 
                sa.Column('automation_config', postgresql.JSONB(astext_type=sa.Text()), nullable=True)
            )


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'company_profiles' in tables:
        columns = [col['name'] for col in inspector.get_columns('company_profiles')]
        
        # Drop automation_config column if it exists
        if 'automation_config' in columns:
            op.drop_column('company_profiles', 'automation_config')


