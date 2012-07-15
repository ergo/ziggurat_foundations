"""change primary key sizes

Revision ID: 53927300c277
Revises: 54d08f9adc8c
Create Date: 2012-06-05 23:33:17.943844

"""

# revision identifiers, used by Alembic.
revision = '53927300c277'
down_revision = '54d08f9adc8c'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('resources', 'resource_id',
                    type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('resources', 'parent_id',
                    type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('users_resources_permissions', 'resource_id',
                    type_=sa.Integer(), existing_type=sa.BigInteger())
    op.alter_column('groups_resources_permissions', 'resource_id',
                    type_=sa.Integer(), existing_type=sa.BigInteger())


def downgrade():
    pass