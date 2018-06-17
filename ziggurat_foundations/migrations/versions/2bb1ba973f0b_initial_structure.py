"""initial table layout

Revision ID: 2bb1ba973f0b
Revises: None
Create Date: 2011-11-10 22:32:14.464939

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op

# downgrade revision identifier, used by Alembic.
revision = "2bb1ba973f0b"
down_revision = None


def upgrade():
    op.create_table(
        "groups",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("group_name", sa.Unicode(50), unique=True),
        sa.Column("description", sa.Text()),
        sa.Column("member_count", sa.Integer, nullable=False, default=0),
    )
    op.create_table(
        "groups_permissions",
        sa.Column(
            "group_name",
            sa.Unicode(50),
            sa.ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("perm_name", sa.Unicode(30), primary_key=True),
    )

    op.create_table(
        "users",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("user_name", sa.Unicode(30), unique=True),
        sa.Column("user_password", sa.Unicode(40)),
        sa.Column("email", sa.Unicode(100), nullable=False, unique=True),
        sa.Column("status", sa.SmallInteger(), nullable=False),
        sa.Column("security_code", sa.Unicode(40), default="default"),
        sa.Column(
            "last_login_date",
            sa.TIMESTAMP(timezone=False),
            default=sa.sql.func.now(),
            server_default=sa.func.now(),
        ),
    )

    op.create_table(
        "users_permissions",
        sa.Column(
            "user_name",
            sa.Unicode(50),
            sa.ForeignKey("users.user_name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("perm_name", sa.Unicode(30), primary_key=True),
    )

    op.create_table(
        "users_groups",
        sa.Column(
            "group_name",
            sa.Unicode(50),
            sa.ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "user_name",
            sa.Unicode(30),
            sa.ForeignKey("users.user_name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
    )

    op.create_table(
        "resources",
        sa.Column(
            "resource_id",
            sa.BigInteger(),
            primary_key=True,
            nullable=False,
            autoincrement=True,
        ),
        sa.Column("resource_name", sa.Unicode(100), nullable=False),
        sa.Column("resource_type", sa.Unicode(30), nullable=False),
        sa.Column(
            "owner_group_name",
            sa.Unicode(50),
            sa.ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="SET NULL"),
        ),
        sa.Column(
            "owner_user_name",
            sa.Unicode(30),
            sa.ForeignKey("users.user_name", onupdate="CASCADE", ondelete="SET NULL"),
        ),
    )

    op.create_table(
        "groups_resources_permissions",
        sa.Column(
            "group_name",
            sa.Unicode(50),
            sa.ForeignKey("groups.group_name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "resource_id",
            sa.BigInteger(),
            sa.ForeignKey(
                "resources.resource_id", onupdate="CASCADE", ondelete="CASCADE"
            ),
            primary_key=True,
            autoincrement=False,
        ),
        sa.Column("perm_name", sa.Unicode(50), primary_key=True),
    )

    op.create_table(
        "users_resources_permissions",
        sa.Column(
            "user_name",
            sa.Unicode(50),
            sa.ForeignKey("users.user_name", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column(
            "resource_id",
            sa.BigInteger(),
            sa.ForeignKey(
                "resources.resource_id", onupdate="CASCADE", ondelete="CASCADE"
            ),
            primary_key=True,
            autoincrement=False,
        ),
        sa.Column("perm_name", sa.Unicode(50), primary_key=True),
    )


def downgrade():
    pass
