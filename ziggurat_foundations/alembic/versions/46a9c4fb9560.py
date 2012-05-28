"""make password hash field bigger

Revision ID: 46a9c4fb9560
Revises: 5c84d7260c5
Create Date: 2011-12-20 17:59:16.961112

"""

# downgrade revision identifier, used by Alembic.
down_revision = '5c84d7260c5'

from alembic.op import *
import sqlalchemy as sa

def upgrade():
    alter_column('users', 'user_password',
                 type_=sa.String(256), existing_type=sa.String(40))
    alter_column('users', 'security_code',
                 type_=sa.String(256), existing_type=sa.String(40))

def downgrade():
    alter_column('users', 'user_password',
                 type_=sa.String(40), existing_type=sa.String(256))
    alter_column('users', 'security_code',
                 type_=sa.String(40), existing_type=sa.String(256))
