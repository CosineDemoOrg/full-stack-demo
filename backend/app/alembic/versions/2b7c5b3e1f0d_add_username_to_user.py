"""Add username to user

Revision ID: 2b7c5b3e1f0d
Revises: 1a31ce608336
Create Date: 2026-02-18

"""

from alembic import op
import sqlalchemy as sa
import sqlmodel.sql.sqltypes


# revision identifiers, used by Alembic.
revision = "2b7c5b3e1f0d"
down_revision = "1a31ce608336"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "user",
        sa.Column("username", sqlmodel.sql.sqltypes.AutoString(), nullable=True),
    )
    op.execute('UPDATE "user" SET username = email WHERE username IS NULL')
    op.alter_column("user", "username", nullable=False)
    op.create_index(op.f("ix_user_username"), "user", ["username"], unique=True)


def downgrade():
    op.drop_index(op.f("ix_user_username"), table_name="user")
    op.drop_column("user", "username")
