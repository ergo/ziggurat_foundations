import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel
from .services.user_permission import UserPermissionManager


class UserPermissionMixin(UserPermissionManager, BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_permissions'

    @declared_attr
    def user_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(30), primary_key=True)

    def __repr__(self):
        return '<UserPermission: %s>' % self.perm_name
