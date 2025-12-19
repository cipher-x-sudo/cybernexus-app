"""Create admin user

Revision ID: 002_admin
Revises: 001_initial
Create Date: 2024-01-01 00:01:00.000000

"""
from alembic import op
import sqlalchemy as sa
from passlib.context import CryptContext
import uuid

# revision identifiers, used by Alembic.
revision = '002_admin'
down_revision = '001_initial'
branch_labels = None
depends_on = None

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def upgrade() -> None:
    # Create admin user
    admin_id = str(uuid.uuid4())
    hashed_password = pwd_context.hash("admin123")
    
    op.execute(
        sa.text("""
            INSERT INTO users (id, username, email, hashed_password, full_name, role, disabled, created_at, updated_at)
            VALUES (:id, :username, :email, :hashed_password, :full_name, :role, :disabled, NOW(), NOW())
        """).bindparams(
            id=admin_id,
            username="admin",
            email="admin@cybernexus.io",
            hashed_password=hashed_password,
            full_name="Admin User",
            role="admin",
            disabled=False
        )
    )


def downgrade() -> None:
    op.execute(
        sa.text("DELETE FROM users WHERE username = 'admin'")
    )

