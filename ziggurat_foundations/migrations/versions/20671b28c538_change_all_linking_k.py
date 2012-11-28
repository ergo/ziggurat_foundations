"""change all linking keys from chars to id's

Revision ID: 20671b28c538
Revises: 4c10d97c509
Create Date: 2012-07-07 21:49:21.906150

"""

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
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        insp = Inspector.from_engine(c.connection.engine)

    op.drop_constraint('groups_pkey', 'groups', type='primary')
    if isinstance(c.connection.engine.dialect, MySQLDialect):
        op.add_column('groups', sa.Column('id', sa.Integer, primary_key=True,
                                      autoincrement=False))
        op.execute("ALTER TABLE groups ADD CONSTRAINT groups_pkey PRIMARY KEY(id)")
        op.execute("ALTER TABLE groups MODIFY id INT NOT NULL AUTO_INCREMENT;")
    else:
        op.add_column('groups', sa.Column('id', sa.Integer, primary_key=True,
                                      autoincrement=True))
        op.execute("ALTER TABLE groups ADD CONSTRAINT groups_pkey PRIMARY KEY(id)")

    if isinstance(c.connection.engine.dialect, MySQLDialect):
        insp = Inspector.from_engine(c.connection.engine)
        for t in ['groups_permissions', 'groups_resources_permissions', 'users_groups']:
            for constraint in insp.get_foreign_keys(t):
                if constraint['referred_columns'] == ['group_name']:
                    op.drop_constraint(constraint['name'], t, type='foreignkey')
        for t in ['users_resources_permissions', 'users_permissions', 'users_groups']:
            for constraint in insp.get_foreign_keys(t):
                if constraint['referred_columns'] == ['user_name']:
                    op.drop_constraint(constraint['name'], t, type='foreignkey')
        for constraint in insp.get_foreign_keys('resources'):
            if constraint['referred_columns'] in [['user_name'], ['group_name']]:
                op.drop_constraint(constraint['name'], 'resources', type='foreignkey')

    op.add_column('resources', sa.Column('owner_user_id', sa.Integer(),
                            sa.ForeignKey('users.id', onupdate='CASCADE',
                                          ondelete='SET NULL')))
    op.add_column('resources', sa.Column('owner_group_id', sa.Integer(),
                            sa.ForeignKey('groups.id', onupdate='CASCADE',
                                          ondelete='SET NULL')))
    op.execute('''update resources set owner_user_id = 
                (select id from users where users.user_name=owner_user_name)''')
    op.execute('''update resources set owner_group_id = 
                (select id from users where users.user_name=owner_group_name)''')

    op.add_column('groups_permissions', sa.Column('group_id', sa.Integer(),
                    sa.ForeignKey('groups.id', onupdate='CASCADE',
                                  ondelete='CASCADE')))
    op.execute('''update groups_permissions set group_id = 
    (select id from groups where groups.group_name=groups_permissions.group_name)''')
    op.drop_constraint('groups_permissions_pkey', 'groups_permissions', type='primary')
    op.execute("ALTER TABLE groups_permissions ADD CONSTRAINT groups_permissions_pkey PRIMARY KEY(group_id,perm_name)")


    op.add_column('groups_resources_permissions', sa.Column('group_id', sa.Integer(),
                    sa.ForeignKey('groups.id', onupdate='CASCADE',
                                  ondelete='CASCADE')))

    op.execute('''update groups_resources_permissions set group_id = 
    (select id from groups where groups.group_name=groups_resources_permissions.group_name)''')
    op.drop_constraint('groups_resources_permissions_pkey', 'groups_resources_permissions', type='primary')
    op.execute("ALTER TABLE groups_resources_permissions ADD CONSTRAINT groups_resources_permissions_pkey PRIMARY KEY(group_id, resource_id , perm_name)")

    op.add_column('users_groups', sa.Column('group_id', sa.Integer(),
                                sa.ForeignKey('groups.id', onupdate='CASCADE',
                                              ondelete='CASCADE')))
    op.execute('''update users_groups set group_id = 
    (select id from groups where groups.group_name=users_groups.group_name)''')


    op.add_column('users_groups', sa.Column('user_id', sa.Integer(),
                                sa.ForeignKey('users.id', onupdate='CASCADE',
                                              ondelete='CASCADE')))
    op.execute('''update users_groups set user_id = 
    (select id from users where users.user_name=users_groups.user_name)''')
    op.drop_constraint('users_groups_pkey', 'users_groups', type='primary')
    op.execute("ALTER TABLE users_groups ADD CONSTRAINT users_groups_pkey PRIMARY KEY(user_id, group_id)")

    op.add_column('users_permissions', sa.Column('user_id', sa.Integer(),
                                sa.ForeignKey('users.id', onupdate='CASCADE',
                                              ondelete='CASCADE')))
    op.execute('''update users_permissions set user_id = 
    (select id from groups where groups.group_name=users_permissions.user_name)''')
    op.drop_constraint('users_permissions_pkey', 'users_permissions', type='primary')
    op.execute("ALTER TABLE users_permissions ADD CONSTRAINT users_permissions_pkey PRIMARY KEY(user_id, perm_name)")

    op.add_column('users_resources_permissions', sa.Column('user_id', sa.Integer(),
                                sa.ForeignKey('users.id', onupdate='CASCADE',
                                              ondelete='CASCADE')))
    op.execute('''update users_resources_permissions set user_id = 
    (select id from users where users.user_name=users_resources_permissions.user_name)''')
    op.drop_constraint('users_resources_permissions_pkey', 'users_resources_permissions', type='primary')
    op.execute("ALTER TABLE users_resources_permissions ADD CONSTRAINT users_resources_permissions_pkey PRIMARY KEY(user_id , resource_id , perm_name )")

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
