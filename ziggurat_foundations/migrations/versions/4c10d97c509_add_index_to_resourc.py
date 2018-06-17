"""add index to resources

Revision ID: 4c10d97c509
Revises: 3cfc41c4a5f0
Create Date: 2012-06-27 03:09:12.392704

"""
from __future__ import unicode_literals

from alembic import op

# revision identifiers, used by Alembic.
revision = "4c10d97c509"
down_revision = "3cfc41c4a5f0"


def upgrade():
    op.create_index("owner_user_name_ix", "resources", ["owner_user_name"])
    op.create_index("owner_group_name_ix", "resources", ["owner_group_name"])


def downgrade():
    pass
