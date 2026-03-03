"""Add organizations, memberships and org_id to items

Revision ID: 202510280001
Revises: 1a31ce608336
Create Date: 2025-10-28 00:01:00
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = "202510280001"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    # Create organization table
    op.create_table(
        "organization",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create membership table
    op.create_table(
        "membership",
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("org_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["user.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["org_id"], ["organization.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    # Add org_id to item
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

    # Data backfill: create a personal org for each user and assign items
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
    op.execute(
        """
        CREATE TEMP TABLE user_org_map (user_id uuid, org_id uuid);
        INSERT INTO user_org_map (user_id, org_id)
        SELECT id, uuid_generate_v4() FROM "user";

        INSERT INTO organization (id, name)
        SELECT m.org_id, CONCAT('Personal - ', u.email)
        FROM user_org_map m
        JOIN "user" u ON u.id = m.user_id;

        INSERT INTO membership (id, user_id, org_id, role)
        SELECT uuid_generate_v4(), m.user_id, m.org_id, 'admin'
        FROM user_org_map m;
        """
    )

    # Assign existing items to an org based on owner mapping
    op.execute(
        """
        UPDATE item
        SET org_id = m.org_id
        FROM membership m
        WHERE m.user_id = item.owner_id
        """
    )

    # Make org_id not null
    op.alter_column("item", "org_id", nullable=False)


def downgrade():
    op.drop_constraint("item_org_id_fkey", "item", type_="foreignkey")
    op.drop_column("item", "org_id")
    op.drop_table("membership")
    op.drop_table("organization")