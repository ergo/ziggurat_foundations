import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel
from ..managers import UserResourcePermissionManager

class UserResourcePermissionMixin(UserResourcePermissionManager, BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_resources_permissions'

    @declared_attr
    def user_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('users.id',
                                                   onupdate='CASCADE',
                                                   ondelete='CASCADE'),
                         primary_key=True)

    @declared_attr
    def resource_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('resources.resource_id',
                                       onupdate='CASCADE',
                                       ondelete='CASCADE'),
                         primary_key=True,
                         autoincrement=False)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(50), primary_key=True)

    def __repr__(self):
        return '<userResourcePermission: %s, %s, %s>' % (self.user_id,
                                                         self.perm_name,
                                                         self.resource_id,)