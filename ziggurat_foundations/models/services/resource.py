from __future__ import unicode_literals
import sqlalchemy as sa
from . import BaseService
from ..base import get_db_session
from ...permissions import (ANY_PERMISSION,
                            ALL_PERMISSIONS,
                            PermissionTuple,
                            resource_permissions_for_users)


class ResourceService(BaseService):
    @classmethod
    def perms_for_user(cls, instance, user, db_session=None):
        """ returns all permissions that given user has for this resource
            from groups and directly set ones too"""
        db_session = get_db_session(db_session, instance)
        query = db_session.query(
            cls.models_proxy.GroupResourcePermission.group_id.label(
                'owner_id'),
            cls.models_proxy.GroupResourcePermission.perm_name,
            sa.literal('group').label('type'))
        query = query.filter(
            cls.models_proxy.GroupResourcePermission.group_id.in_(
                [gr.id for gr in user.groups]
            )
        )
        query = query.filter(
            cls.models_proxy.GroupResourcePermission.resource_id ==
            instance.resource_id)

        query2 = db_session.query(
            cls.models_proxy.UserResourcePermission.user_id.label('owner_id'),
            cls.models_proxy.UserResourcePermission.perm_name,
            sa.literal('user').label('type'))
        query2 = query2.filter(
            cls.models_proxy.UserResourcePermission.user_id ==
            user.id)
        query2 = query2.filter(
            cls.models_proxy.UserResourcePermission.resource_id ==
            instance.resource_id)
        query = query.union(query2)

        groups_dict = dict([(g.id, g) for g in user.groups])
        perms = [PermissionTuple(user,
                                 row.perm_name,
                                 row.type,
                                 groups_dict.get(row.owner_id) if
                                 row.type == 'group' else None,
                                 instance, False, True) for row in query]

        # include all perms if user is the owner of this resource
        if instance.owner_user_id == user.id:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'user',
                                         None, instance, True, True))
        groups_dict = dict([(g.id, g) for g in user.groups])
        if instance.owner_group_id in groups_dict:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                         groups_dict.get(
                                             instance.owner_group_id),
                                         instance, True, True))

        return perms

    @classmethod
    def direct_perms_for_user(cls, instance, user, db_session=None):
        """ returns permissions that given user has for this resource
            without ones inherited from groups that user belongs to"""
        db_session = get_db_session(db_session, instance)
        query = db_session.query(
            cls.models_proxy.UserResourcePermission.user_id,
            cls.models_proxy.UserResourcePermission.perm_name)
        query = query.filter(cls.models_proxy.UserResourcePermission.user_id ==
                             user.id)
        query = query.filter(
            cls.models_proxy.UserResourcePermission.resource_id ==
            instance.resource_id)

        perms = [PermissionTuple(user,
                                 row.perm_name,
                                 'user',
                                 None,
                                 instance, False, True) for row in query]

        # include all perms if user is the owner of this resource
        if instance.owner_user_id == user.id:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'user',
                                         None, instance, True))
        return perms

    @classmethod
    def group_perms_for_user(cls, instance, user, db_session=None):
        """ returns permissions that given user has for this resource
            that are inherited from groups """
        db_session = get_db_session(db_session, instance)
        perms = resource_permissions_for_users(cls.models_proxy,
                                               ANY_PERMISSION,
                                               resource_ids=[
                                                   instance.resource_id],
                                               user_ids=[user.id],
                                               db_session=db_session)
        perms = [p for p in perms if p.type == 'group']
        # include all perms if user is the owner of this resource
        groups_dict = dict([(g.id, g) for g in user.groups])
        if instance.owner_group_id in groups_dict:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                         groups_dict.get(
                                             instance.owner_group_id),
                                         instance, True, True))
        return perms

    @classmethod
    def users_for_perm(cls, instance, perm_name, user_ids=None, group_ids=None,
                       limit_group_permissions=False, skip_group_perms=False,
                       db_session=None):
        """ return PermissionTuples for users AND groups that have given
        permission for the resource, perm_name is __any_permission__ then
        users with any permission will be listed
        user_ids - limits the permissions to specific user ids,
        group_ids - limits the permissions to specific group ids,
        limit_group_permissions - should be used if we do not want to have
        user objects returned for group permissions, this might cause performance
        issues for big groups
        skip_group_perms - do not attach group permissions to the resultset
        """
        db_session = get_db_session(db_session, instance)
        users_perms = resource_permissions_for_users(cls.models_proxy,
                                                     [perm_name],
                                                     [instance.resource_id],
                                                     user_ids=user_ids,
                                                     group_ids=group_ids,
                                                     limit_group_permissions=limit_group_permissions,
                                                     skip_group_perms=skip_group_perms,
                                                     db_session=db_session)
        if instance.owner_user_id:
            users_perms.append(
                PermissionTuple(instance.owner,
                                ALL_PERMISSIONS, 'user', None, instance, True,
                                True))
        if instance.owner_group_id and not skip_group_perms:
            for user in instance.owner_group.users:
                users_perms.append(
                    PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                    instance.owner_group, instance, True,
                                    True))

        return users_perms

    @classmethod
    def by_resource_id(cls, resource_id, db_session=None):
        """ fetch the resouce by id """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model).filter(cls.model.resource_id ==
                                                   int(resource_id))
        return query.first()

    @classmethod
    def perm_by_group_and_perm_name(cls, resource_id, group_id, perm_name,
                                    db_session=None):
        """ fetch permissions by group and permission name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls.models_proxy.GroupResourcePermission)
        query = query.filter(
            cls.models_proxy.GroupResourcePermission.group_id == group_id)
        query = query.filter(
            cls.models_proxy.GroupResourcePermission.perm_id == perm_name)
        query = query.filter(
            cls.models_proxy.GroupResourcePermission.resource_id == resource_id)
        return query.first()

    @classmethod
    def groups_for_perm(cls, instance, perm_name, group_ids=None,
                        limit_group_permissions=False,
                        db_session=None):
        """ return PermissionTuples for groups that have given
        permission for the resource, perm_name is __any_permission__ then
        users with any permission will be listed
        user_ids - limits the permissions to specific user ids,
        group_ids - limits the permissions to specific group ids,
        """
        db_session = get_db_session(db_session, instance)
        group_perms = resource_permissions_for_users(cls.models_proxy,
                                                     [perm_name],
                                                     [instance.resource_id],
                                                     group_ids=group_ids,
                                                     limit_group_permissions=limit_group_permissions,
                                                     skip_user_perms=True,
                                                     db_session=db_session)
        if instance.owner_group_id:
            for user in instance.owner_group.users:
                group_perms.append(
                    PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                    instance.owner_group, instance, True,
                                    True))

        return group_perms

    @classmethod
    def subtree_deeper(cls, object_id, limit_depth=1000000, flat=True,
                       db_session=None):
        """ This returns you subree of ordered objects relative
        to the start object id currently only postgresql
        """
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 as depth, array[ordering] as sorting FROM
                    resources res WHERE res.resource_id = :id
                  UNION ALL
                    SELECT res_u.*, depth+1 as depth,
                    (st.sorting || ARRAY[res_u.ordering] ) as sort
                    FROM resources res_u, subtree st
                    WHERE res_u.parent_id = st.resource_id
            )
            SELECT * FROM subtree WHERE depth<=:depth ORDER BY sorting;
        """
        db_session = get_db_session(db_session)
        q = db_session.query(cls).from_statement(raw_q).params(id=object_id,
                                                               depth=limit_depth)
        return q

    @classmethod
    def path_upper(cls, object_id, limit_depth=1000000, flat=True,
                   db_session=None):
        """ This returns you path to root node starting from object_id
            currently only for postgresql
        """
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 as depth FROM resources res
                    WHERE res.resource_id = :id
                  UNION ALL
                    SELECT res_u.*, depth+1 as depth
                    FROM resources res_u, subtree st
                    WHERE res_u.resource_id = st.parent_id
            )
            SELECT * FROM subtree WHERE depth<=:depth;
        """
        db_session = get_db_session(db_session)
        q = db_session.query(cls).from_statement(raw_q).params(id=object_id,
                                                               depth=limit_depth)
        return q
