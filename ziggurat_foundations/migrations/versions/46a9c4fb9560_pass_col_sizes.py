"""make password hash field bigger

Revision ID: 46a9c4fb9560
Revises: 5c84d7260c5
Create Date: 2011-12-20 17:59:16.961112

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

# downgrade revision identifier, used by Alembic.
revision = "46a9c4fb9560"
down_revision = "5c84d7260c5"


def upgrade():
    op.alter_column(
        "users", "user_password", type_=sa.Unicode(256), existing_type=sa.Unicode(40)
    )
    op.alter_column(
        "users", "security_code", type_=sa.Unicode(256), existing_type=sa.Unicode(40)
    )


def downgrade():
    pass
