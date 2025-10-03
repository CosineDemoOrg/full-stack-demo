"""Add organizations, memberships, and org_id to items

Revision ID: 20251003_add_orgs
Revises: d98dd8ec85a3
Create Date: 2025-10-03

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import sqlmodel.sql.sqltypes

# revision identifiers, used by Alembic.
revision = "20251003_add_orgs"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Ensure uuid extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create organization table
    op.create_table(
        "organization",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("uuid_generate_v4()")),
    )
    op.create_index(op.f("ix_organization_name"), "organization", ["name"], unique=False)

    # Create membership table
    op.create_table(
        "membership",
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text("uuid_generate_v4()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
    )
    op.create_index(op.f("ix_membership_user_id"), "membership", ["user_id"], unique=False)
    op.create_index(op.f("ix_membership_org_id"), "membership", ["org_id"], unique=False)

    # Add org_id column to item
    op.add_column(
        "item",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key("item_org_id_fkey", "item", "organization", ["org_id"], ["id"], ondelete="CASCADE")
    op.create_index(op.f("ix_item_org_id"), "item", ["org_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_item_org_id"), table_name="item")
    op.drop_constraint("item_org_id_fkey", "item", type_="foreignkey")
    op.drop_column("item", "org_id")

    op.drop_index(op.f("ix_membership_org_id"), table_name="membership")
    op.drop_index(op.f("ix_membership_user_id"), table_name="membership")
    op.drop_table("membership")

    op.drop_index(op.f("ix_organization_name"), table_name="organization")
    op.drop_table("organization")