"""Add organizations, memberships and item.org_id

Revision ID: 7b2a1f0c9ab1
Revises: 1a31ce608336
Create Date: 2025-10-27 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = '7b2a1f0c9ab1'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'organization',
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table(
        'membership',
        sa.Column('role', sa.String(length=50), nullable=False),
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_membership_user_org_unique', 'membership', ['user_id', 'org_id'], unique=True)

    # add org_id to item (nullable for back-compat)
    op.add_column('item', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'item', 'organization', ['org_id'], ['id'], ondelete='CASCADE')


def downgrade():
    op.drop_constraint(None, 'item', type_='foreignkey')
    op.drop_column('item', 'org_id')
    op.drop_index('ix_membership_user_org_unique', table_name='membership')
    op.drop_table('membership')
    op.drop_table('organization')