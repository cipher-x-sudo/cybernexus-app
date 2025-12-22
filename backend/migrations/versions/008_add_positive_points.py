
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '008_positive_points'
down_revision = '007_jobs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Add status and resolution fields to findings table
    if 'findings' in tables:
        # Check if columns already exist
        columns = [col['name'] for col in inspector.get_columns('findings')]
        
        if 'status' not in columns:
            op.add_column('findings', sa.Column('status', sa.String(length=20), nullable=False, server_default='active'))
        
        if 'resolved_at' not in columns:
            op.add_column('findings', sa.Column('resolved_at', sa.DateTime(timezone=True), nullable=True))
        
        if 'resolved_by' not in columns:
            op.add_column('findings', sa.Column('resolved_by', sa.String(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True))
        
        # Create index on status
        indexes = [idx['name'] for idx in inspector.get_indexes('findings')]
        if 'ix_findings_status' not in indexes:
            op.create_index('ix_findings_status', 'findings', ['status'])
        if 'idx_finding_user_status' not in indexes:
            op.create_index('idx_finding_user_status', 'findings', ['user_id', 'status'])
    
    # Create positive_indicators table
    if 'positive_indicators' not in tables:
        op.create_table(
            'positive_indicators',
            sa.Column('id', sa.String(length=255), primary_key=True),
            sa.Column('user_id', sa.String(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('indicator_type', sa.String(length=50), nullable=False),
            sa.Column('category', sa.String(length=50), nullable=False),
            sa.Column('points_awarded', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
            sa.Column('target', sa.String(length=500), nullable=True),
            sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
            sa.PrimaryKeyConstraint('id')
        )
        
        # Create indexes
        op.create_index('ix_positive_indicators_user_id', 'positive_indicators', ['user_id'])
        op.create_index('ix_positive_indicators_type', 'positive_indicators', ['indicator_type'])
        op.create_index('ix_positive_indicators_category', 'positive_indicators', ['category'])
        op.create_index('ix_positive_indicators_created_at', 'positive_indicators', ['created_at'])
        op.create_index('idx_positive_user_category', 'positive_indicators', ['user_id', 'category'])
    else:
        # Table exists, check and create missing indexes
        existing_indexes = [idx['name'] for idx in inspector.get_indexes('positive_indicators')]
        
        if 'ix_positive_indicators_user_id' not in existing_indexes:
            try:
                op.create_index('ix_positive_indicators_user_id', 'positive_indicators', ['user_id'])
            except Exception:
                pass
        if 'ix_positive_indicators_type' not in existing_indexes:
            try:
                op.create_index('ix_positive_indicators_type', 'positive_indicators', ['indicator_type'])
            except Exception:
                pass
        if 'ix_positive_indicators_category' not in existing_indexes:
            try:
                op.create_index('ix_positive_indicators_category', 'positive_indicators', ['category'])
            except Exception:
                pass
        if 'ix_positive_indicators_created_at' not in existing_indexes:
            try:
                op.create_index('ix_positive_indicators_created_at', 'positive_indicators', ['created_at'])
            except Exception:
                pass
        if 'idx_positive_user_category' not in existing_indexes:
            try:
                op.create_index('idx_positive_user_category', 'positive_indicators', ['user_id', 'category'])
            except Exception:
                pass


def downgrade() -> None:
    conn = op.get_bind()
    inspector = inspect(conn)
    tables = inspector.get_table_names()
    
    # Drop positive_indicators table
    if 'positive_indicators' in tables:
        indexes = [idx['name'] for idx in inspector.get_indexes('positive_indicators')]
        for idx_name in indexes:
            try:
                op.drop_index(idx_name, table_name='positive_indicators')
            except Exception:
                pass
        op.drop_table('positive_indicators')
    
    # Remove columns from findings table
    if 'findings' in tables:
        columns = [col['name'] for col in inspector.get_columns('findings')]
        indexes = [idx['name'] for idx in inspector.get_indexes('findings')]
        
        if 'idx_finding_user_status' in indexes:
            try:
                op.drop_index('idx_finding_user_status', table_name='findings')
            except Exception:
                pass
        
        if 'ix_findings_status' in indexes:
            try:
                op.drop_index('ix_findings_status', table_name='findings')
            except Exception:
                pass
        
        if 'resolved_by' in columns:
            op.drop_column('findings', 'resolved_by')
        
        if 'resolved_at' in columns:
            op.drop_column('findings', 'resolved_at')
        
        if 'status' in columns:
            op.drop_column('findings', 'status')

