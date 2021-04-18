"""change primary key sizes

Revision ID: 53927300c277
Revises: 54d08f9adc8c
Create Date: 2012-06-05 23:33:17.943844

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op
from alembic.context import get_context
from sqlalchemy.dialects.mysql.base import MySQLDialect

# revision identifiers, used by Alembic.
revision = "53927300c277"
down_revision = "54d08f9adc8c"


def upgrade():
    c = get_context()
    # drop foreign keys for mysql
    kwargs = {}
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        kwargs["autoincrement"] = True
        insp = sa.inspect(c.connection.engine)
        for t in [
            "groups_resources_permissions",
            "users_resources_permissions",
            "resources",
        ]:
            for constraint in insp.get_foreign_keys(t):
                if constraint["referred_columns"] == ["resource_id"]:
                    op.drop_constraint(constraint["name"], t, type_="foreignkey")



    op.alter_column(
        "resources",
        "resource_id",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        nullable=False,
        **kwargs
    )
    op.alter_column(
        "resources", "parent_id", type_=sa.Integer(), existing_type=sa.BigInteger()
    )
    op.alter_column(
        "users_resources_permissions",
        "resource_id",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        nullable=False,
    )
    op.alter_column(
        "groups_resources_permissions",
        "resource_id",
        type_=sa.Integer(),
        existing_type=sa.BigInteger(),
        nullable=False,
    )

    # recreate foreign keys for mysql
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.create_foreign_key(
            "groups_resources_permissions_resource_fk",
            "groups_resources_permissions",
            "resources",
            ["resource_id"],
            ["resource_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        )
        op.create_foreign_key(
            "users_resources_permissions_fk",
            "users_resources_permissions",
            "resources",
            ["resource_id"],
            ["resource_id"],
            onupdate="CASCADE",
            ondelete="CASCADE",
        )


def downgrade():
    pass
