"""add organizations and memberships, add org_id to items

Revision ID: 2025_11_03_add_orgs
Revises: d98dd8ec85a3_edit_replace_id_integers_in_all_models_
Create Date: 2025-11-03

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "2025_11_03_add_orgs"
down_revision = "d98dd8ec85a3_edit_replace_id_integers_in_all_models_"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_organization_name"), "organization", ["name"], unique=True)

    op.create_table(
        "membership",
        sa.Column("role", sa.String(length=255), nullable=False),
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("org_id", sa.UUID(), nullable=False),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_membership_user_id"), "membership", ["user_id"], unique=False)
    op.create_index(op.f("ix_membership_org_id"), "membership", ["org_id"], unique=False)

    # add org_id to items
    op.add_column("item", sa.Column("org_id", sa.UUID(), nullable=True))
    op.create_index(op.f("ix_item_org_id"), "item", ["org_id"], unique=False)
    op.create_foreign_key(
        "item_org_id_fkey", source_table="item", referent_table="organization", local_cols=["org_id"], remote_cols=["id"], ondelete="CASCADE"
    )
    # optional: backfill org_id for existing items by creating a default org per owner is complex.
    # Leave as NULL and enforce at application level for new inserts.

def downgrade() -> None:
    # remove item org constraint and column
    op.drop_constraint("item_org_id_fkey", "item", type_="foreignkey")
    op.drop_index(op.f("ix_item_org_id"), table_name="item")
    op.drop_column("item", "org_id")
    # drop memberships and organizations
    op.drop_index(op.f("ix_membership_org_id"), table_name="membership")
    op.drop_index(op.f("ix_membership_user_id"), table_name="membership")
    op.drop_table("membership")
    op.drop_index(op.f("ix_organization_name"), table_name="organization")
    op.drop_table("organization")