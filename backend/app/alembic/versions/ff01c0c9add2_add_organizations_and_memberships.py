"""Add organizations and memberships, scope items by organization

Revision ID: ff01c0c9add2
Revises: d98dd8ec85a3
Create Date: 2025-01-01 00:00:00.000000

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "ff01c0c9add2"
down_revision = "d98dd8ec85a3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "organization",
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v4()"),
        ),
        sa.Column(
            "owner_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            nullable=False,
        ),
    )

    op.create_table(
        "membership",
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("user.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organization.id", ondelete="CASCADE"),
            primary_key=True,
            nullable=False,
        ),
        sa.Column("role", sa.String(length=50), nullable=False, server_default="member"),
    )

    op.add_column(
        "item",
        sa.Column(
            "org_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organization.id", ondelete="CASCADE"),
            nullable=True,
        ),
    )

    # For existing rows, set org_id to NULL; in new deployments, seed data will populate properly.
    # Once populated, enforce non-null constraint.
    op.alter_column("item", "org_id", nullable=False)


def downgrade() -> None:
    op.drop_constraint("item_org_id_fkey", "item", type_="foreignkey")
    op.drop_column("item", "org_id")
    op.drop_table("membership")
    op.drop_table("organization")