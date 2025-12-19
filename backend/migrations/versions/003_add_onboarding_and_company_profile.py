"""Add onboarding_completed and company_profiles table (if not in initial schema)

Revision ID: 003_onboarding
Revises: 002_admin
Create Date: 2024-01-01 00:02:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '003_onboarding'
down_revision = '002_admin'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if onboarding_completed column already exists (for fresh installs with updated initial schema)
    conn = op.get_bind()
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('users')]
    
    if 'onboarding_completed' not in columns:
        op.add_column('users', sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'))
    
    # Check if company_profiles table already exists
    tables = inspector.get_table_names()
    if 'company_profiles' not in tables:
        op.create_table(
            'company_profiles',
            sa.Column('id', sa.String(), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, unique=True),
            sa.Column('name', sa.String(length=200), nullable=False),
            sa.Column('industry', sa.String(length=100), nullable=True),
            sa.Column('company_size', sa.String(length=50), nullable=True),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('phone', sa.String(length=50), nullable=True),
            sa.Column('email', sa.String(length=255), nullable=True),
            sa.Column('website', sa.String(length=500), nullable=True),
            sa.Column('primary_domain', sa.String(length=255), nullable=True),
            sa.Column('additional_domains', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('ip_ranges', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('key_assets', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('address', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('logo_url', sa.String(length=500), nullable=True),
            sa.Column('timezone', sa.String(length=50), nullable=True, server_default='UTC'),
            sa.Column('locale', sa.String(length=10), nullable=True, server_default='en-US'),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        op.create_index('idx_company_profile_user', 'company_profiles', ['user_id'], unique=True)
        op.create_index('ix_company_profiles_user_id', 'company_profiles', ['user_id'], unique=True)


def downgrade() -> None:
    # Only drop if exists
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    if 'company_profiles' in tables:
        op.drop_table('company_profiles')
    
    columns = [col['name'] for col in inspector.get_columns('users')]
    if 'onboarding_completed' in columns:
        op.drop_column('users', 'onboarding_completed')

