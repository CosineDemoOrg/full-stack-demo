"""Add organizations, memberships and item.org_id

Revision ID: fe12b3c4a567
Revises: 1a31ce608336
Create Date: 2025-10-23 00:00:00

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision = 'fe12b3c4a567'
down_revision = '1a31ce608336'
branch_labels = None
depends_on = None


def upgrade():
    # Ensure uuid extension
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    # Create organization table
    op.create_table(
        'organization',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(length=255), nullable=False),
    )

    # Create membership table
    op.create_table(
        'membership',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False, server_default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=20), nullable=False, server_default='member'),
        sa.Column('accepted', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['org_id'], ['organization.id'], ondelete='CASCADE'),
    )

    # Add org_id to item table
    op.add_column('item', sa.Column('org_id', postgresql.UUID(as_uuid=True), nullable=True))
    op.create_foreign_key(None, 'item', 'organization', ['org_id'], ['id'], ondelete='CASCADE')

    # Backfill org_id for existing items by creating a default org for each owner
    # For simplicity, create a single org per user and assign existing items to it
    op.execute("""
        DO $$
        DECLARE
            u RECORD;
            new_org UUID;
        BEGIN
            FOR u IN SELECT id FROM "user" LOOP
                new_org := uuid_generate_v4();
                INSERT INTO organization (id, name) VALUES (new_org, 'Default Org ' || substr(u.id::text, 1, 8));
                INSERT INTO membership (user_id, org_id, role, accepted) VALUES (u.id, new_org, 'admin', true);
                UPDATE item SET org_id = new_org WHERE owner_id = u.id;
            END LOOP;
        END$$;
    """)

    # Make org_id not null now that it's backfilled
    op.alter_column('item', 'org_id', nullable=False)


def downgrade():
    op.drop_constraint(None, 'item', type_='foreignkey')
    op.drop_column('item', 'org_id')
    op.drop_table('membership')
    op.drop_table('organization')