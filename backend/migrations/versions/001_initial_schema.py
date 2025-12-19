"""Initial schema

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('username', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('hashed_password', sa.String(length=255), nullable=False),
        sa.Column('full_name', sa.String(length=255), nullable=True),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='user'),
        sa.Column('disabled', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('onboarding_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_user_username', 'users', ['username'], unique=True)
    op.create_index('idx_user_email', 'users', ['email'], unique=True)
    
    # Create entities table
    op.create_table(
        'entities',
        sa.Column('id', sa.String(length=255), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('type', sa.String(length=50), nullable=False),
        sa.Column('value', sa.String(length=500), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False, server_default='info'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_entity_user_type', 'entities', ['user_id', 'type'])
    op.create_index('idx_entity_user_value', 'entities', ['user_id', 'value'])
    op.create_index('ix_entities_user_id', 'entities', ['user_id'])
    op.create_index('ix_entities_type', 'entities', ['type'])
    op.create_index('ix_entities_value', 'entities', ['value'])
    
    # Create graph_nodes table
    op.create_table(
        'graph_nodes',
        sa.Column('id', sa.String(length=255), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('entity_id', sa.String(length=255), sa.ForeignKey('entities.id', ondelete='CASCADE'), nullable=True),
        sa.Column('label', sa.String(length=500), nullable=False),
        sa.Column('node_type', sa.String(length=50), nullable=False),
        sa.Column('data', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_graph_node_user', 'graph_nodes', ['user_id'])
    op.create_index('idx_graph_node_user_type', 'graph_nodes', ['user_id', 'node_type'])
    op.create_index('ix_graph_nodes_user_id', 'graph_nodes', ['user_id'])
    op.create_index('ix_graph_nodes_entity_id', 'graph_nodes', ['entity_id'])
    op.create_index('ix_graph_nodes_node_type', 'graph_nodes', ['node_type'])
    
    # Create graph_edges table
    op.create_table(
        'graph_edges',
        sa.Column('id', sa.String(length=255), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('source_id', sa.String(length=255), sa.ForeignKey('graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('target_id', sa.String(length=255), sa.ForeignKey('graph_nodes.id', ondelete='CASCADE'), nullable=False),
        sa.Column('relation', sa.String(length=50), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_graph_edge_user', 'graph_edges', ['user_id'])
    op.create_index('idx_graph_edge_source_target', 'graph_edges', ['source_id', 'target_id'])
    op.create_index('idx_graph_edge_relation', 'graph_edges', ['user_id', 'relation'])
    op.create_index('ix_graph_edges_user_id', 'graph_edges', ['user_id'])
    op.create_index('ix_graph_edges_source_id', 'graph_edges', ['source_id'])
    op.create_index('ix_graph_edges_target_id', 'graph_edges', ['target_id'])
    op.create_index('ix_graph_edges_relation', 'graph_edges', ['relation'])
    
    # Create user_activity_logs table
    op.create_table(
        'user_activity_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('action', sa.String(length=100), nullable=False),
        sa.Column('resource_type', sa.String(length=50), nullable=True),
        sa.Column('resource_id', sa.String(length=255), nullable=True),
        sa.Column('ip_address', sa.String(length=45), nullable=True),
        sa.Column('user_agent', sa.Text(), nullable=True),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_activity_user_timestamp', 'user_activity_logs', ['user_id', 'timestamp'])
    op.create_index('idx_activity_action', 'user_activity_logs', ['action', 'timestamp'])
    op.create_index('ix_user_activity_logs_user_id', 'user_activity_logs', ['user_id'])
    op.create_index('ix_user_activity_logs_action', 'user_activity_logs', ['action'])
    op.create_index('ix_user_activity_logs_resource_type', 'user_activity_logs', ['resource_type'])
    op.create_index('ix_user_activity_logs_resource_id', 'user_activity_logs', ['resource_id'])
    op.create_index('ix_user_activity_logs_timestamp', 'user_activity_logs', ['timestamp'])
    
    # Create network_logs table
    op.create_table(
        'network_logs',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=True),
        sa.Column('request_id', sa.String(length=255), nullable=False, unique=True),
        sa.Column('ip', sa.String(length=45), nullable=True),
        sa.Column('method', sa.String(length=10), nullable=False),
        sa.Column('path', sa.String(length=1000), nullable=False),
        sa.Column('query', sa.Text(), nullable=True),
        sa.Column('status', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Float(), nullable=False),
        sa.Column('tunnel_detection', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('response_headers', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('request_body', sa.Text(), nullable=True),
        sa.Column('response_body', sa.Text(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_network_user_timestamp', 'network_logs', ['user_id', 'timestamp'])
    op.create_index('idx_network_ip_timestamp', 'network_logs', ['ip', 'timestamp'])
    op.create_index('idx_network_path_timestamp', 'network_logs', ['path', 'timestamp'])
    op.create_index('ix_network_logs_user_id', 'network_logs', ['user_id'])
    op.create_index('ix_network_logs_request_id', 'network_logs', ['request_id'], unique=True)
    op.create_index('ix_network_logs_ip', 'network_logs', ['ip'])
    op.create_index('ix_network_logs_method', 'network_logs', ['method'])
    op.create_index('ix_network_logs_path', 'network_logs', ['path'])
    op.create_index('ix_network_logs_status', 'network_logs', ['status'])
    op.create_index('ix_network_logs_timestamp', 'network_logs', ['timestamp'])
    
    # Create findings table
    op.create_table(
        'findings',
        sa.Column('id', sa.String(length=255), primary_key=True),
        sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('capability', sa.String(length=50), nullable=False),
        sa.Column('severity', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=500), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('affected_assets', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_score', sa.Float(), nullable=True),
        sa.Column('target', sa.String(length=500), nullable=True),
        sa.Column('discovered_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_finding_user_severity', 'findings', ['user_id', 'severity'])
    op.create_index('idx_finding_user_capability', 'findings', ['user_id', 'capability'])
    op.create_index('idx_finding_discovered', 'findings', ['discovered_at'])
    op.create_index('ix_findings_user_id', 'findings', ['user_id'])
    op.create_index('ix_findings_capability', 'findings', ['capability'])
    op.create_index('ix_findings_severity', 'findings', ['severity'])
    op.create_index('ix_findings_discovered_at', 'findings', ['discovered_at'])
    
    # Create company_profiles table
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
    op.drop_table('company_profiles')
    op.drop_table('findings')
    op.drop_table('network_logs')
    op.drop_table('user_activity_logs')
    op.drop_table('graph_edges')
    op.drop_table('graph_nodes')
    op.drop_table('entities')
    op.drop_table('users')

