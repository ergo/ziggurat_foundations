"""add registered_date to user

Revision ID: 54d08f9adc8c
Revises: 2d472fe79b95
Create Date: 2012-03-10 11:12:39.353857

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql.base import PGDialect

# revision identifiers, used by Alembic.
revision = "54d08f9adc8c"
down_revision = "2d472fe79b95"


def upgrade():
    from alembic.context import get_context

    c = get_context()
    if isinstance(c.connection.engine.dialect, PGDialect):
        op.add_column(
            "users",
            sa.Column(
                "registered_date",
                sa.TIMESTAMP(timezone=False),
                default=sa.sql.func.now(),
                server_default=sa.func.now(),
            ),
        )
    else:
        op.add_column(
            "users",
            sa.Column(
                "registered_date",
                sa.TIMESTAMP(timezone=False),
                default=sa.sql.func.now(),
            ),
        )


def downgrade():
    pass
