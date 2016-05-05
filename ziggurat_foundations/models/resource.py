from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel
from .services.resource import ResourceService
from .base import get_db_session


class ResourceMixin(BaseModel):
    __possible_permissions__ = ()

    _ziggurat_service = ResourceService

    @declared_attr
    def __tablename__(self):
        return 'resources'

    @declared_attr
    def resource_id(self):
        return sa.Column(sa.Integer(), primary_key=True, nullable=False,
                         autoincrement=True)

    @declared_attr
    def parent_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('resources.resource_id',
                                       onupdate='CASCADE',
                                       ondelete='SET NULL'))

    @declared_attr
    def ordering(self):
        return sa.Column(sa.Integer(), default=0, nullable=False)

    @declared_attr
    def resource_name(self):
        return sa.Column(sa.Unicode(100), nullable=False)

    @declared_attr
    def resource_type(self):
        return sa.Column(sa.Unicode(30), nullable=False)

    @declared_attr
    def owner_group_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('groups.id', onupdate='CASCADE',
                                       ondelete='SET NULL'), index=True)

    @declared_attr
    def owner_user_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='SET NULL'), index=True)

    @declared_attr
    def group_permissions(self):
        """ returns all group permissions for this resource"""
        return sa.orm.relationship('GroupResourcePermission',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def user_permissions(self):
        """ returns all user permissions for this resource"""
        return sa.orm.relationship('UserResourcePermission',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def groups(self):
        """ returns all groups that have permissions for this resource"""
        return sa.orm.relationship('Group',
                                   secondary='groups_resources_permissions',
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def users(self):
        """ returns all users that have permissions for this resource"""
        return sa.orm.relationship('User',
                                   secondary='users_resources_permissions',
                                   passive_deletes=True,
                                   passive_updates=True)

    __mapper_args__ = {'polymorphic_on': resource_type}
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    def __repr__(self):
        return '<Resource: %s, %s, id: %s>' % (self.resource_type,
                                               self.resource_name,
                                               self.resource_id,)

    @property
    def __acl__(self):
        raise Exception("The model should have implemented __acl__")

    @sa.orm.validates('user_permissions', 'group_permissions')
    def validate_permission(self, key, permission):
        """ validate if resouce can have specific permission """
        if permission.perm_name not in self.__possible_permissions__:
            raise AssertionError('perm_name is not one of {}'.format(
                self.__possible_permissions__))
        return permission

    def perms_for_user(self, user, db_session=None):
        db_session = get_db_session(db_session, self)
        return ResourceService.perms_for_user(
            self, user=user, db_session=db_session)

    def direct_perms_for_user(self, user, db_session=None):
        db_session = get_db_session(db_session, self)
        return ResourceService.direct_perms_for_user(
            self, user=user, db_session=db_session)

    def group_perms_for_user(self, user, db_session=None):
        db_session = get_db_session(db_session, self)
        return ResourceService.group_perms_for_user(
            self, user=user, db_session=db_session)

    def users_for_perm(self, perm_name, user_ids=None, group_ids=None,
                       limit_group_permissions=False, skip_group_perms=False,
                       db_session=None):
        db_session = get_db_session(db_session, self)
        return ResourceService.users_for_perm(
            self, perm_name, user_ids=user_ids, group_ids=group_ids,
            limit_group_permissions=limit_group_permissions,
            skip_group_perms=skip_group_perms, db_session=db_session)

    @classmethod
    def by_resource_id(cls, resource_id, db_session=None):
        db_session = get_db_session(db_session)
        return ResourceService.by_resource_id(resource_id=resource_id,
                                              db_session=db_session)

    @classmethod
    def perm_by_group_and_perm_name(cls, res_id, group_id, perm_name,
                                    db_session=None):
        db_session = get_db_session(db_session)
        return ResourceService.perm_by_group_and_perm_name(
            resource_id=res_id, group_id=group_id, perm_name=perm_name,
            db_session=db_session)

    def groups_for_perm(self, perm_name, group_ids=None,
                        limit_group_permissions=False,
                        db_session=None):
        db_session = get_db_session(db_session, self)
        return ResourceService.groups_for_perm(
            self, perm_name=perm_name, group_ids=group_ids,
            limit_group_permissions=limit_group_permissions,
            db_session=db_session)

    @classmethod
    def subtree_deeper(cls, object_id, limit_depth=1000000, flat=True,
                       db_session=None):
        db_session = get_db_session(db_session)
        return ResourceService.subtree_deeper(
            object_id=object_id, limit_depth=limit_depth, flat=flat,
            db_session=db_session)

    @classmethod
    def path_upper(cls, object_id, limit_depth=1000000, flat=True,
                   db_session=None):
        db_session = get_db_session(db_session)
        return ResourceService.path_upper(
            object_id=object_id, limit_depth=limit_depth, flat=flat,
            db_session=db_session)
