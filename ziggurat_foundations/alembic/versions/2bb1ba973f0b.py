"""initial table layout

Revision ID: 2bb1ba973f0b
Revises: None
Create Date: 2011-11-10 22:32:14.464939

"""

# downgrade revision identifier, used by Alembic.
down_revision = None

from alembic.op import *
import sqlalchemy as sa

def upgrade():
    create_table('groups',
                 sa.Column('id', sa.Integer, primary_key=True,
                           autoincrement=True),
                 sa.Column('group_name', sa.Unicode(50), unique=True),
                 sa.Column('description', sa.Text()),
                 sa.Column('member_count', sa.Integer, nullable=False,
                           default=0)
                 )
    create_table('groups_permissions',
                 sa.Column('group_name', sa.Unicode(50),
                        sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True),
                 sa.Column('perm_name', sa.Unicode(30), primary_key=True)
                 )
    # TODO
    # CONSTRAINT groups_permissions_perm_name_check 
    # CHECK (perm_name::text = lower(perm_name::text))
    
        
    create_table('users',
                 sa.Column('id', sa.Integer, primary_key=True,
                           autoincrement=True),
                 sa.Column('user_name', sa.Unicode(30), unique=True),
                 sa.Column('user_password', sa.String(40)),
                 sa.Column('email', sa.Unicode(100), nullable=False,
                           unique=True),
                 sa.Column('status', sa.SmallInteger(), nullable=False),
                 sa.Column('security_code', sa.String(40), default='default'),
                 sa.Column('last_login_date', sa.TIMESTAMP(timezone=False),
                                default=sa.sql.func.now(),
                                server_default=sa.func.now()
                                )
                 )
    # TODO for postgresql
#CREATE UNIQUE INDEX users_email_key
#  ON users
#  USING btree
#  (lower(email::text));
#
#-- Index: users_username_uq
#
#-- DROP INDEX users_username_uq;
#
#CREATE INDEX users_username_uq
#  ON users
#  USING btree
#  (lower(user_name::text));

    
    create_table('users_permissions',
                 sa.Column('user_name', sa.Unicode(50),
                         sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True),
                 sa.Column('perm_name', sa.Unicode(30), primary_key=True)
                 )
    
    create_table('users_groups',
                 sa.Column('group_name', sa.Unicode(50),
                         sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True),
                 sa.Column('user_name', sa.Unicode(30),
                        sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True)
                 )

    create_table('resources',
                 sa.Column('resource_id', sa.BigInteger(), primary_key=True,
                           nullable=False, autoincrement=True),
                 sa.Column('resource_name', sa.Unicode(100), nullable=False),
                 sa.Column('resource_type', sa.Unicode(30), nullable=False),
                 sa.Column('owner_group_name', sa.Unicode(50),
                       sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                     ondelete='SET NULL')),
                 sa.Column('owner_user_name', sa.Unicode(30),
                       sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                     ondelete='SET NULL'))
                 )

    create_table('groups_resources_permissions',
                 sa.Column('group_name', sa.Unicode(50),
                           sa.ForeignKey('groups.group_name',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                           primary_key=True),
                 sa.Column('resource_id', sa.BigInteger(),
                           sa.ForeignKey('resources.resource_id',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                           primary_key=True,
                           autoincrement=False),
                 sa.Column('perm_name', sa.Unicode(50), primary_key=True)
                 )
    # TODO for postgresql
    # CONSTRAINT groups_resources_permissions_perm_name_check 
    # CHECK (perm_name::text = lower(perm_name::text))


    create_table('users_resources_permissions',
                 sa.Column('user_name', sa.Unicode(50),
                           sa.ForeignKey('users.user_name',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                           primary_key=True),
                 sa.Column('resource_id', sa.BigInteger(),
                           sa.ForeignKey('resources.resource_id',
                                         onupdate='CASCADE',
                                         ondelete='CASCADE'),
                           primary_key=True,
                           autoincrement=False),
                 sa.Column('perm_name', sa.Unicode(50), primary_key=True)
                 )

    # TODO for postgresql
    # CONSTRAINT users_resources_permissions_perm_name_check 
    # CHECK (perm_name::text = lower(perm_name::text))

def downgrade():
    # Operations to reverse the above upgrade go here.
    drop_table('users_resources_permissions')
    drop_table('groups_resources_permissions')
    drop_table('resources')
    drop_table('users_groups')
    drop_table('users_permissions')
    drop_table('users')
    drop_table('groups_permissions')
    drop_table('groups')
