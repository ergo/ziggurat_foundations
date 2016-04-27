from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel


class UserGroupMixin(BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_groups'

    @declared_attr
    def group_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('groups.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def user_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    def __repr__(self):
        return '<UserGroup: g:%s, u:%s>' % (self.group_id, self.user_id,)
