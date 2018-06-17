"""add security_code_date

Revision ID: 13391c68750
Revises: 438c27ec1c9
Create Date: 2015-06-14 21:28:30.672968

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "13391c68750"
down_revision = "438c27ec1c9"


def upgrade():
    op.add_column(
        "users",
        sa.Column(
            "security_code_date", sa.DateTime(), server_default="2000-01-01 01:01"
        ),
    )


def downgrade():
    pass
