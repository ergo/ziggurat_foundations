"""add lower() indexes to pg

Revision ID: 439766f6104d
Revises: 20671b28c538
Create Date: 2012-07-09 21:33:28.404627

"""
from __future__ import unicode_literals

from alembic import op
from alembic.context import get_context
from sqlalchemy.dialects.postgresql.base import PGDialect

# revision identifiers, used by Alembic.
revision = "439766f6104d"
down_revision = "20671b28c538"


def upgrade():
    c = get_context()
    if isinstance(c.connection.engine.dialect, PGDialect):
        op.execute(
            """
        CREATE UNIQUE INDEX groups_unique_group_name_key
          ON groups
          USING btree
          (lower(group_name::text));
          """
        )

        op.execute(
            """
        ALTER TABLE groups_permissions
            ADD CONSTRAINT groups_permissions_perm_name_check CHECK (perm_name::text = lower(perm_name::text));
        """
        )  # noqa

        op.execute(
            """
        ALTER TABLE groups_resources_permissions
              ADD CONSTRAINT groups_resources_permissions_perm_name_check CHECK (perm_name::text = lower(perm_name::text));
        """
        )  # noqa

        op.execute(
            """
        ALTER TABLE users_permissions
          ADD CONSTRAINT user_permissions_perm_name_check CHECK (perm_name::text = lower(perm_name::text));
        """
        )  # noqa

        op.execute(
            """
        ALTER TABLE users_resources_permissions
          ADD CONSTRAINT users_resources_permissions_perm_name_check CHECK (perm_name::text = lower(perm_name::text));
        """
        )  # noqa

        op.execute(
            """
        CREATE UNIQUE INDEX users_email_key2 ON users (lower(email::text));
        """
        )

        op.execute(
            """
        CREATE INDEX users_username_uq2 ON users (lower(user_name::text));
        """
        )


def downgrade():
    pass
