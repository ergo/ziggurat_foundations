"""add local_user_id

Revision ID: 57bbf0c387c
Revises: 13391c68750
Create Date: 2016-04-02 09:54:09.643644

"""
from __future__ import unicode_literals

import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import table

# revision identifiers, used by Alembic.
revision = "57bbf0c387c"
down_revision = "13391c68750"


def upgrade():
    conn = op.get_bind()
    op.add_column("external_identities", sa.Column("local_user_id", sa.Integer()))

    external_identities_t = table(
        "external_identities",
        sa.Column("local_user_name", sa.Unicode(50)),
        sa.Column("local_user_id", sa.Integer),
    )
    users_t = table(
        "users", sa.Column("user_name", sa.Unicode(50)), sa.Column("id", sa.Integer)
    )

    stmt = (
        external_identities_t.update()
        .values(local_user_id=users_t.c.id)
        .where(users_t.c.user_name == external_identities_t.c.local_user_name)
    )
    conn.execute(stmt)
    op.drop_constraint("pk_external_identities", "external_identities", type_="primary")
    op.drop_constraint(
        "fk_external_identities_local_user_name_users",
        "external_identities",
        type_="foreignkey",
    )
    op.drop_column("external_identities", "local_user_name")
    op.create_primary_key(
        "pk_external_identities",
        "external_identities",
        columns=["external_id", "local_user_id", "provider_name"],
    )
    op.create_foreign_key(
        None,
        "external_identities",
        "users",
        remote_cols=["id"],
        local_cols=["local_user_id"],
        onupdate="CASCADE",
        ondelete="CASCADE",
    )


def downgrade():
    pass
