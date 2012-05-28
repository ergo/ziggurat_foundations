"""add registered_date to user

Revision ID: 54d08f9adc8c
Revises: 2d472fe79b95
Create Date: 2012-03-10 11:12:39.353857

"""

# revision identifiers, used by Alembic.
revision = '54d08f9adc8c'
down_revision = '2d472fe79b95'

from alembic.op import *
import sqlalchemy as sa


def upgrade():
    add_column('users', sa.Column('registered_date',
                                  sa.TIMESTAMP(timezone=False),
                                  default=sa.sql.func.now(),
                                  server_default=sa.func.now()))

def downgrade():
    drop_column('users', 'registered_date')
