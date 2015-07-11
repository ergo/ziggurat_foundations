import sqlalchemy as sa
from paginate_sqlalchemy import SqlalchemyOrmPage
from . import ModelManager
from ...utils import get_db_session
from ...permissions import (ANY_PERMISSION,
                            ALL_PERMISSIONS,
                            PermissionTuple)


class GroupManager(ModelManager):
    @classmethod
    def all(cls, db_session=None):
        """ return all groups"""
        query = get_db_session(db_session).query(cls)
        return query

    @classmethod
    def by_group_name(cls, group_name, db_session=None):
        """ fetch group by name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.group_name == group_name)
        return query.first()

    @sa.orm.validates('permissions')
    def validate_permission(self, key, permission):
        """ validates if group can get assigned with permission"""
        assert permission.perm_name in self.__possible_permissions__
        return permission

    def get_user_paginator(self, page=1, item_count=None, items_per_page=50,
                           user_ids=None, GET_params=None):
        """ returns paginator over users belonging to the group"""
        if not GET_params:
            GET_params = {}
        GET_params.pop('page', None)
        query = self.users_dynamic
        if user_ids:
            query = query.filter(self._ziggurat_models.UserGroup.user_id.in_(user_ids))
        return SqlalchemyOrmPage(query, page=page, item_count=item_count,
                                 items_per_page=items_per_page,
                                 **GET_params)

    def resources_with_possible_perms(self, perm_names=None, resource_ids=None,
                                      resource_types=None,
                                      db_session=None):
        """ returns list of permissions and resources for this group,
            resource_ids restricts the search to specific resources"""
        db_session = get_db_session(db_session, self)
        perms = []

        query = db_session.query(self._ziggurat_models.GroupResourcePermission.perm_name,
                                 self._ziggurat_models.Group,
                                 self._ziggurat_models.Resource
        )
        query = query.filter(
            self._ziggurat_models.Resource.resource_id == self._ziggurat_models.GroupResourcePermission.resource_id)
        query = query.filter(
            self._ziggurat_models.Group.id == self._ziggurat_models.GroupResourcePermission.group_id)
        if resource_ids:
            query = query.filter(
                self._ziggurat_models.GroupResourcePermission.resource_id.in_(resource_ids))

        if resource_types:
            query = query.filter(
                self._ziggurat_models.Resource.resource_type.in_(resource_types))

        if (perm_names not in (
                [ANY_PERMISSION], ANY_PERMISSION) and perm_names):
            query = query.filter(
                self._ziggurat_models.GroupResourcePermission.perm_name.in_(perm_names))
        query = query.filter(self._ziggurat_models.GroupResourcePermission.group_id == self.id)

        perms = [PermissionTuple(None, row.perm_name, 'group',
                                 self, row.Resource, False, True)
                 for row in query]
        for resource in self.resources:
            perms.append(PermissionTuple(None, ALL_PERMISSIONS, 'group', self,
                                         resource, True, True))
        return perms