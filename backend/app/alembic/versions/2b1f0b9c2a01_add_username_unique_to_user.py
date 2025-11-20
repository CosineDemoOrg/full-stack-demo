"""Add username column with unique index to User

Revision ID: 2b1f0b9c2a01
Revises: d98dd8ec85a3
Create Date: 2025-11-20 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2b1f0b9c2a01"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade():
    # Add nullable column first
    op.add_column("user", sa.Column("username", sa.String(length=255), nullable=True))
    # Backfill username with email for existing rows to satisfy NOT NULL + uniqueness
    op.execute('UPDATE "user" SET username = email WHERE username IS NULL')
    # Make column not nullable
    op.alter_column("user", "username", nullable=False)
    # Create unique index
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_column("user", "username")