"""Add organizations, memberships and org_id to items

Revision ID: 2_multi_tenant_orgs
Revises: d98dd8ec85a3
Create Date: 2025-01-01 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "2_multi_tenant_orgs"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "organization",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("uuid_generate_v4()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "membership",
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["user.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["org_id"],
            ["organization.id"],
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_id", "org_id"),
    )

    op.add_column(
        "item",
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=True),
    )
    op.create_foreign_key(
        "item_org_id_fkey",
        "item",
        "organization",
        ["org_id"],
        ["id"],
        ondelete="CASCADE",
    )

    op.execute(
        """
        WITH first_org AS (
            INSERT INTO organization (name) VALUES ('Default Organization')
            RETURNING id
        )
        UPDATE item
        SET org_id = (SELECT id FROM first_org)
        """
    )

    op.alter_column("item", "org_id", nullable=False)


def downgrade():
    op.drop_constraint("item_org_id_fkey", "item", type_="foreignkey")
    op.drop_column("item", "org_id")
    op.drop_table("membership")
    op.drop_table("organization")