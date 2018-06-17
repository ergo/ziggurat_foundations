"""bigger identity datatypes

Revision ID: 2d472fe79b95
Revises: 264049f80948
Create Date: 2012-02-19 17:24:24.422312

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = "2d472fe79b95"
down_revision = "264049f80948"


def upgrade():
    op.alter_column(
        "external_identities",
        "external_id",
        type_=sa.Unicode(255),
        existing_type=sa.Unicode(50),
        nullable=False,
    )
    op.alter_column(
        "external_identities",
        "external_user_name",
        type_=sa.Unicode(255),
        existing_type=sa.Unicode(50),
    )


def downgrade():
    pass
