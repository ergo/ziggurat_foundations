"""change all linking keys from chars to id's

Revision ID: 20671b28c538
Revises: 4c10d97c509
Create Date: 2012-07-07 21:49:21.906150

"""
from __future__ import unicode_literals

# revision identifiers, used by Alembic.
revision = '20671b28c538'
down_revision = '4c10d97c509'

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.mysql.base import MySQLDialect
from alembic.context import get_context
from sqlalchemy.engine.reflection import Inspector


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

    # inspected keys
    groups_permissions_pkey = insp.get_pk_constraint('groups_permissions')['name']
    groups_pkey = insp.get_pk_constraint('groups')['name']
    groups_resources_permissions_pkey = insp.get_pk_constraint('groups_resources_permissions')['name']
    users_groups_pkey = insp.get_pk_constraint('users_groups')['name']
    users_permissions_pkey = insp.get_pk_constraint('users_permissions')['name']
    users_resources_permissions_pkey = insp.get_pk_constraint('users_resources_permissions')['name']



    op.drop_constraint('groups_pkey', 'groups', type_='primary')

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('groups', sa.Column('id', sa.Integer, primary_key=True, autoincrement=False))
        op.create_primary_key(groups_pkey, 'groups', cols=['id'])
        op.alter_column('groups', 'id', type_=sa.Integer, existing_type=sa.Integer, autoincrement=True,
                        existing_autoincrement=False, nullable=False)
    else:
        op.add_column('groups', sa.Column('id', sa.Integer, primary_key=True, autoincrement=True))
        op.create_primary_key(groups_pkey, 'groups', cols=['id'])

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        for t in ['groups_permissions', 'groups_resources_permissions', 'users_groups']:
            for constraint in insp.get_foreign_keys(t):
                if constraint['referred_columns'] == ['group_name']:
                    op.drop_constraint(constraint['name'], t, type_='foreignkey')

        for t in ['users_resources_permissions', 'users_permissions', 'users_groups']:
            for constraint in insp.get_foreign_keys(t):
                if constraint['referred_columns'] == ['user_name']:
                    op.drop_constraint(constraint['name'], t, type_='foreignkey')

        for constraint in insp.get_foreign_keys('resources'):
            if constraint['referred_columns'] in [['user_name'], ['group_name']]:
                op.drop_constraint(constraint['name'], 'resources', type_='foreignkey')

    op.add_column('resources', sa.Column('owner_user_id', sa.Integer(),
                            sa.ForeignKey('users.id', onupdate='CASCADE',
                                          ondelete='SET NULL')))
    op.add_column('resources', sa.Column('owner_group_id', sa.Integer(),
                            sa.ForeignKey('groups.id', onupdate='CASCADE',
                                          ondelete='SET NULL')))
    # update the data
    op.execute('''update resources set owner_user_id = 
                (select id from users where users.user_name=owner_user_name)''')
    op.execute('''update resources set owner_group_id = 
                (select id from users where users.user_name=owner_group_name)''')

    # mysql is stupid as usual so we cant create FKEY and add PKEY later,
    # need to set PKEY first and then set FKEY
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('groups_permissions', sa.Column('group_id', sa.Integer()))
    else:
        op.add_column('groups_permissions', sa.Column('group_id', sa.Integer(),
                    sa.ForeignKey('groups.id', onupdate='CASCADE',
                                  ondelete='CASCADE')))

    op.execute('''update groups_permissions set group_id = 
    (select id from groups where groups.group_name=groups_permissions.group_name)''')

    op.drop_constraint(groups_permissions_pkey, 'groups_permissions', type_='primary')
    op.create_primary_key(groups_permissions_pkey, 'groups_permissions',
                          cols=['group_id', 'perm_name'])
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.create_foreign_key(None, 'groups_permissions', 'groups',
                              remote_cols=['id'],
                              local_cols=['group_id'], onupdate='CASCADE',
                              ondelete='CASCADE')

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('groups_resources_permissions',
                      sa.Column('group_id', sa.Integer()))
    else:
        op.add_column('groups_resources_permissions', sa.Column('group_id', sa.Integer(),
                    sa.ForeignKey('groups.id', onupdate='CASCADE',
                                  ondelete='CASCADE')))

    op.execute('''update groups_resources_permissions set group_id = 
    (select id from groups where groups.group_name=groups_resources_permissions.group_name)''')
    op.drop_constraint(groups_resources_permissions_pkey, 'groups_resources_permissions',
                       type_='primary')
    op.create_primary_key(groups_resources_permissions_pkey, 'groups_resources_permissions',
                          cols=['group_id', 'resource_id' , 'perm_name'])

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.create_foreign_key(None, 'groups_resources_permissions', 'groups',
                              remote_cols=['id'],
                              local_cols=['group_id'], onupdate='CASCADE',
                              ondelete='CASCADE')

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('users_groups', sa.Column('group_id', sa.Integer()))
    else:
        op.add_column('users_groups', sa.Column('group_id', sa.Integer(),
                                    sa.ForeignKey('groups.id', onupdate='CASCADE',
                                                  ondelete='CASCADE')))
    op.execute('''update users_groups set group_id = 
    (select id from groups where groups.group_name=users_groups.group_name)''')


    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('users_groups', sa.Column('user_id', sa.Integer()))
    else:
        op.add_column('users_groups', sa.Column('user_id', sa.Integer(),
                                    sa.ForeignKey('users.id', onupdate='CASCADE',
                                                  ondelete='CASCADE')))
    op.execute('''update users_groups set user_id = 
    (select id from users where users.user_name=users_groups.user_name)''')
    op.drop_constraint(users_groups_pkey, 'users_groups', type='primary')
    op.create_primary_key(users_groups_pkey, 'users_groups',
                          cols=['user_id', 'group_id'])
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.create_foreign_key(None, 'users_groups', 'groups',
                              remote_cols=['id'],
                              local_cols=['group_id'], onupdate='CASCADE',
                              ondelete='CASCADE')
        op.create_foreign_key(None, 'users_groups', 'users',
                              remote_cols=['id'],
                              local_cols=['user_id'], onupdate='CASCADE',
                              ondelete='CASCADE')

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('users_permissions', sa.Column('user_id', sa.Integer()))
    else:
        op.add_column('users_permissions', sa.Column('user_id', sa.Integer(),
                                    sa.ForeignKey('users.id', onupdate='CASCADE',
                                                  ondelete='CASCADE')))
    op.execute('''update users_permissions set user_id = 
    (select id from groups where groups.group_name=users_permissions.user_name)''')
    op.drop_constraint(users_permissions_pkey, 'users_permissions', type='primary')
    op.create_primary_key(users_permissions_pkey, 'users_permissions',
                          cols=['user_id', 'perm_name'])
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.create_foreign_key(None, 'users_permissions', 'users',
                              remote_cols=['id'],
                              local_cols=['user_id'], onupdate='CASCADE',
                              ondelete='CASCADE')

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('users_resources_permissions', sa.Column('user_id', sa.Integer()))
    else:
        op.add_column('users_resources_permissions', sa.Column('user_id', sa.Integer(),
                                    sa.ForeignKey('users.id', onupdate='CASCADE',
                                                  ondelete='CASCADE')))

    op.execute('''update users_resources_permissions set user_id = 
    (select id from users where users.user_name=users_resources_permissions.user_name)''')
    op.drop_constraint(users_resources_permissions_pkey, 'users_resources_permissions',
                       type='primary')
    op.create_primary_key(users_resources_permissions_pkey, 'users_resources_permissions',
                          cols=['user_id', 'resource_id', 'perm_name'])
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.create_foreign_key(None, 'users_resources_permissions', 'users',
                              remote_cols=['id'],
                              local_cols=['user_id'], onupdate='CASCADE',
                              ondelete='CASCADE')

    op.drop_column('resources', 'owner_user_name')
    op.drop_column('resources', 'owner_group_name')
    op.drop_column('groups_permissions', 'group_name')
    op.drop_column('groups_resources_permissions', 'group_name')
    op.drop_column('users_resources_permissions', 'user_name')
    op.drop_column('users_groups', 'group_name')
    op.drop_column('users_groups', 'user_name')
    op.drop_column('users_permissions', 'user_name')


def downgrade():
    pass
