"""Add scheduled searches table

Revision ID: 009_scheduled_searches
Revises: 008_positive_points
Create Date: 2024-01-20 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '009_scheduled_searches'
down_revision = '008_positive_points'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'scheduled_searches' not in tables:
        op.create_table(
            'scheduled_searches',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('capability', sa.String(length=50), nullable=False),
            sa.Column('target', sa.String(length=500), nullable=False),
            sa.Column('config', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('schedule_type', sa.String(length=20), nullable=False, server_default='cron'),
            sa.Column('cron_expression', sa.String(length=100), nullable=True),
            sa.Column('timezone', sa.String(length=50), nullable=False, server_default='UTC'),
            sa.Column('enabled', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('last_run_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('next_run_at', sa.DateTime(timezone=True), nullable=True),
            sa.Column('run_count', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_scheduled_searches_user_id', 'scheduled_searches', ['user_id'])
        op.create_index('ix_scheduled_searches_capability', 'scheduled_searches', ['capability'])
        op.create_index('ix_scheduled_searches_enabled', 'scheduled_searches', ['enabled'])
        op.create_index('ix_scheduled_searches_next_run_at', 'scheduled_searches', ['next_run_at'])
        op.create_index('idx_scheduled_search_user_enabled', 'scheduled_searches', ['user_id', 'enabled'])
        op.create_index('idx_scheduled_search_user_capability', 'scheduled_searches', ['user_id', 'capability'])
        op.create_index('idx_scheduled_search_next_run', 'scheduled_searches', ['next_run_at'])


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'scheduled_searches' in tables:
        indexes = [idx['name'] for idx in inspector.get_indexes('scheduled_searches')]
        for idx_name in indexes:
            try:
                op.drop_index(idx_name, table_name='scheduled_searches')
            except Exception:
                pass
        op.drop_table('scheduled_searches')

