from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from .base import BaseModel


class GroupResourcePermissionMixin(BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups_resources_permissions'

    @declared_attr
    def group_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('groups.id',
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

    @validates('perm_name')
    def validate_perm_name(self, key, value):
        if value != value.lower():
            raise AssertionError('perm_name needs to be lowercase')
        return value

    def __repr__(self):
        return '<GroupResourcePermission: g:%s, %s, r:%s>' % (self.group_id,
                                                              self.perm_name,
                                                              self.resource_id,)
