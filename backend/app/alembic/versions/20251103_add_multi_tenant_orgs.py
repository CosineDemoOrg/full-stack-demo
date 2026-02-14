"""Add multi-tenant organizations, memberships, and org_id on items

Revision ID: 20251103_add_multi_tenant_orgs
Revises: d98dd8ec85a3
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20251103_add_multi_tenant_orgs'
down_revision = 'd98dd8ec85a3'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("description", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "membership",
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add org_id to items
    op.add_column(
        "item",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    # For existing rows, set org_id to NULL; future inserts must provide org_id
    # Make column non-nullable after backfill if desired; here enforce non-null going forward
    op.alter_column("item", "org_id", nullable=False)

    # Optional: index for faster org scoping
    op.create_index("ix_item_org_id", "item", ["org_id"])


def downgrade():
    op.drop_index("ix_item_org_id", table_name="item")
    op.drop_column("item", "org_id")
    op.drop_table("membership")
    op.drop_table("organization")