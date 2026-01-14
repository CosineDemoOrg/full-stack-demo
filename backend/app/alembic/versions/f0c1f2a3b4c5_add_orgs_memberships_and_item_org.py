"""Add organizations, memberships, and org_id to items

Revision ID: f0c1f2a3b4c5
Revises: d98dd8ec85a3
Create Date: 2025-11-13 00:00:00
"""
from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "f0c1f2a3b4c5"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade():
    # Create organization table
    op.create_table(
        "organization",
        sa.Column("name", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organization_name"), "organization", ["name"], unique=True)

    # Create membership table
    op.create_table(
        "membership",
        sa.Column("role", sqlmodel.sql.sqltypes.AutoString(), nullable=False),
        sa.Column("id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("user_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.Column("org_id", sqlmodel.sql.sqltypes.GUID(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_membership_user_id"), "membership", ["user_id"], unique=False)
    op.create_index(op.f("ix_membership_org_id"), "membership", ["org_id"], unique=False)

    # Add org_id column to item table
    op.add_column(
        "item",
        sa.Column("org_id", sqlmodel.sql.sqltypes.GUID(), nullable=True),
    )
    # For existing rows, set org_id to NULL; future code expects NOT NULL, but allow NULL to pass migration
    # Then set NOT NULL constraint
    op.create_foreign_key(
        "item_org_id_fkey",
        "item",
        "organization",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Make org_id not nullable
    op.alter_column("item", "org_id", nullable=False)


def downgrade():
    # Remove org_id from item
    op.drop_constraint("item_org_id_fkey", "item", type_="foreignkey")
    op.drop_column("item", "org_id")

    # Drop membership
    op.drop_index(op.f("ix_membership_org_id"), table_name="membership")
    op.drop_index(op.f("ix_membership_user_id"), table_name="membership")
    op.drop_table("membership")

    # Drop organization
    op.drop_index(op.f("ix_organization_name"), table_name="organization")
    op.drop_table("organization")