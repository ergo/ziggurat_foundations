"""normalize constraint and key names
correct keys for pre 0.5.6 naming convention

Revision ID: 438c27ec1c9
Revises: 439766f6104d
Create Date: 2015-06-13 21:16:32.358778

"""

# revision identifiers, used by Alembic.
revision = '438c27ec1c9'
down_revision = '439766f6104d'

from alembic import op
import sqlalchemy as sa
from alembic.context import get_context
from sqlalchemy.dialects.postgresql.base import PGDialect
from sqlalchemy.engine.reflection import Inspector

# correct keys for pre 0.5.6 naming convention

def upgrade():
    c = get_context()
    insp = Inspector.from_engine(c.connection.engine)
    # existing migration
    # pre naming convention keys
    groups_permissions_pkey = 'groups_permissions_pkey'
    groups_pkey = 'groups_pkey'
    groups_resources_permissions_pkey = 'groups_resources_permissions_pkey'
    users_groups_pkey = 'users_groups_pkey'
    users_permissions_pkey = 'users_permissions_pkey'
    users_resources_permissions_pkey = 'users_resources_permissions_pkey'

    if isinstance(c.connection.engine.dialect, PGDialect):
        op.drop_index('groups_unique_group_name_key', 'groups')
        op.execute('''
        CREATE UNIQUE INDEX ix_groups_uq_group_name_key
          ON groups
          USING btree
          (lower(group_name::text));
          ''')

        op.drop_constraint('groups_permissions_perm_name_check',
                           'groups_permissions')
        op.execute('''
        ALTER TABLE groups_permissions
            ADD CONSTRAINT ck_groups_permissions_perm_name CHECK (perm_name::text = lower(perm_name::text));
        ''')

        op.drop_constraint('groups_resources_permissions_perm_name_check',
                           'groups_resources_permissions')
        op.execute('''
        ALTER TABLE groups_resources_permissions
              ADD CONSTRAINT ck_groups_resources_permissions_perm_name CHECK (perm_name::text = lower(perm_name::text));
        ''')

        op.drop_constraint('user_permissions_perm_name_check',
                           'users_permissions')
        op.execute('''
        ALTER TABLE users_permissions
          ADD CONSTRAINT ck_user_permissions_perm_name CHECK (perm_name::text = lower(perm_name::text));
        ''')

        op.drop_constraint('users_resources_permissions_perm_name_check',
                           'users_resources_permissions')
        op.execute('''
        ALTER TABLE users_resources_permissions
          ADD CONSTRAINT ck_users_resources_permissions_perm_name CHECK (perm_name::text = lower(perm_name::text));
        ''')

        op.drop_index('users_email_key2', 'users')
        op.execute('''
        CREATE UNIQUE INDEX ix_users_uq_lower_email ON users (lower(email::text));
        ''')

        op.drop_index('users_username_uq2', 'users')
        op.execute('''
        CREATE INDEX ix_users_ux_lower_username ON users (lower(user_name::text));
        ''')


        if groups_permissions_pkey == insp.get_pk_constraint('groups_permissions')['name']:
            op.execute('ALTER INDEX groups_permissions_pkey RENAME to pk_groups_permissions')

        if groups_pkey == insp.get_pk_constraint('groups')['name']:
            op.execute('ALTER INDEX groups_pkey RENAME to pk_groups')

        if groups_resources_permissions_pkey == insp.get_pk_constraint('groups_resources_permissions')['name']:
            op.execute('ALTER INDEX groups_resources_permissions_pkey RENAME to pk_groups_resources_permissions')

        if users_groups_pkey == insp.get_pk_constraint('users_groups')['name']:
            op.execute('ALTER INDEX pk_users_groups RENAME to pk_users_groups')

        if users_permissions_pkey == insp.get_pk_constraint('users_permissions')['name']:
            op.execute('ALTER INDEX users_permissions_pkey RENAME to pk_users_permissions')

        if users_resources_permissions_pkey == insp.get_pk_constraint('users_resources_permissions')['name']:
            op.execute('ALTER INDEX users_resources_permissions_pkey RENAME to pk_users_resources_permissions')


def downgrade():
    pass
