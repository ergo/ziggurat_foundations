"""create indices on resource owners

Revision ID: 613e7c11dead
Revises: b5e6dd3449dd
Create Date: 2018-02-15 11:51:29.659352

"""
from __future__ import unicode_literals

from alembic import op

# revision identifiers, used by Alembic.
revision = "613e7c11dead"
down_revision = "b5e6dd3449dd"


def upgrade():
    op.create_index(
        op.f("ix_resources_owner_group_id"), "resources", ["owner_group_id"]
    )
    op.create_index(op.f("ix_resources_owner_user_id"), "resources", ["owner_user_id"])


def downgrade():
    pass
