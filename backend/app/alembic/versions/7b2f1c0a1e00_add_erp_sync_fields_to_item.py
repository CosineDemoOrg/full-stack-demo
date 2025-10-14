"""Add ERP sync fields to item

Revision ID: 7b2f1c0a1e00
Revises: d98dd8ec85a3
Create Date: 2025-10-14

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = "7b2f1c0a1e00"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "item",
        sa.Column("external_id", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.create_index("ix_item_external_id", "item", ["external_id"], unique=False)
    op.add_column("item", sa.Column("synced_at", sa.DateTime(timezone=False), nullable=True))
    op.add_column(
        "item",
        sa.Column("sync_status", sqlmodel.sql.sqltypes.AutoString(), nullable=False, server_default="unsynced"),
    )
    # Remove server_default to keep model defaults clean
    op.alter_column("item", "sync_status", server_default=None)


def downgrade():
    op.drop_index("ix_item_external_id", table_name="item")
    op.drop_column("item", "external_id")
    op.drop_column("item", "synced_at")
    op.drop_column("item", "sync_status")