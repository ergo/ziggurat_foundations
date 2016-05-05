from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from sqlalchemy.orm import validates
from .base import BaseModel
from .services.group_permission import GroupPermissionService
from .base import get_db_session


class GroupPermissionMixin(BaseModel):
    """ group permission mixin """

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    _ziggurat_service = GroupPermissionService

    @declared_attr
    def __tablename__(self):
        return 'groups_permissions'

    @declared_attr
    def group_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('groups.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(64), primary_key=True)

    @validates('perm_name')
    def validate_perm_name(self, key, value):
        if value != value.lower():
            raise AssertionError('perm_name needs to be lowercase')
        return value

    def __repr__(self):
        return '<GroupPermission: %s>' % self.perm_name

    @classmethod
    def by_group_and_perm(cls, group_id, perm_name, db_session=None):
        db_session = get_db_session(db_session)
        return GroupPermissionService.by_group_and_perm(
            group_id=group_id,
            perm_name=perm_name,
            db_session=db_session)
