# -*- coding: utf-8 -*-

from collections import namedtuple

import sqlalchemy as sa

from .models.base import get_db_session

try:
    try:
        from pyramid.authorization import Allow, Deny, ALL_PERMISSIONS
    except ImportError:
        from pyramid.security import Allow, Deny, ALL_PERMISSIONS

except ImportError as e:
    Allow = "Allow"
    Deny = "Deny"

    # borrowed directly from pyramid - to avoid dependency on pyramid itself
    # source https://github.com/Pylons/pyramid/blob/master/pyramid/security.py

    class AllPermissionsList(object):

        """ Stand in 'permission list' to represent all permissions """

        def __iter__(self):
            return ()

        def __contains__(self, other):
            return True

        def __eq__(self, other):
            return isinstance(other, self.__class__)

    ALL_PERMISSIONS = AllPermissionsList()

__all__ = [
    "ANY_PERMISSION_CLS",
    "ANY_PERMISSION",
    "resource_permissions_for_users",
    "permission_to_04_acls",
    "permission_to_pyramid_acls",
]


class ANY_PERMISSION_CLS(object):
    def __eq__(self, other):
        return "__any_permission__" == other

    def __ne__(self, other):
        return "__any_permission__" != other


ANY_PERMISSION = ANY_PERMISSION_CLS()

PermissionTuple = namedtuple(
    "PermissionTuple",
    ["user", "perm_name", "type", "group", "resource", "owner", "allowed"],
)


def resource_permissions_for_users(
    models_proxy,
    perm_names,
    resource_ids=None,
    user_ids=None,
    group_ids=None,
    resource_types=None,
    limit_group_permissions=False,
    skip_user_perms=False,
    skip_group_perms=False,
    db_session=None,
):
    """
    Returns permission tuples that match one of passed permission names
    perm_names - list of permissions that can be matched
    user_ids - restrict to specific users
    group_ids - restrict to specific groups
    resource_ids - restrict to specific resources
    limit_group_permissions - should be used if we do not want to have
    user objects returned for group permissions, this might cause performance
    issues for big groups
    """
    db_session = get_db_session(db_session)

    # fetch groups and their permissions (possibly with users belonging
    # to group if needed)
    query = db_session.query(
        models_proxy.GroupResourcePermission.perm_name,
        models_proxy.User,
        models_proxy.Group,
        sa.literal("group").label("type"),
        models_proxy.Resource,
    )

    query = query.join(
        models_proxy.Group,
        models_proxy.Group.id == models_proxy.GroupResourcePermission.group_id,
    )
    query = query.join(
        models_proxy.Resource,
        models_proxy.Resource.resource_id
        == models_proxy.GroupResourcePermission.resource_id,
    )
    if limit_group_permissions:
        query = query.outerjoin(models_proxy.User, models_proxy.User.id == None)  # noqa
    else:
        query = query.join(
            models_proxy.UserGroup,
            models_proxy.UserGroup.group_id
            == models_proxy.GroupResourcePermission.group_id,
        )

        query = query.outerjoin(
            models_proxy.User, models_proxy.User.id == models_proxy.UserGroup.user_id
        )

    if resource_ids:
        query = query.filter(
            models_proxy.GroupResourcePermission.resource_id.in_(resource_ids)
        )
    if resource_types:
        query = query.filter(models_proxy.Resource.resource_type.in_(resource_types))

    if perm_names not in ([ANY_PERMISSION], ANY_PERMISSION) and perm_names:
        query = query.filter(
            models_proxy.GroupResourcePermission.perm_name.in_(perm_names)
        )
    if group_ids:
        query = query.filter(
            models_proxy.GroupResourcePermission.group_id.in_(group_ids)
        )

    if user_ids and not limit_group_permissions:
        query = query.filter(models_proxy.UserGroup.user_id.in_(user_ids))

    # 2nd query that will fetch users with direct resource permissions
    query2 = db_session.query(
        models_proxy.UserResourcePermission.perm_name,
        models_proxy.User,
        models_proxy.Group,
        sa.literal("user").label("type"),
        models_proxy.Resource,
    )
    query2 = query2.join(
        models_proxy.User,
        models_proxy.User.id == models_proxy.UserResourcePermission.user_id,
    )
    query2 = query2.join(
        models_proxy.Resource,
        models_proxy.Resource.resource_id
        == models_proxy.UserResourcePermission.resource_id,
    )

    # group needs to be present to work for union, but never actually matched
    query2 = query2.outerjoin(models_proxy.Group, models_proxy.Group.id == None)  # noqa
    if perm_names not in ([ANY_PERMISSION], ANY_PERMISSION) and perm_names:
        query2 = query2.filter(
            models_proxy.UserResourcePermission.perm_name.in_(perm_names)
        )
    if resource_ids:
        query2 = query2.filter(
            models_proxy.UserResourcePermission.resource_id.in_(resource_ids)
        )
    if resource_types:
        query2 = query2.filter(models_proxy.Resource.resource_type.in_(resource_types))
    if user_ids:
        query2 = query2.filter(
            models_proxy.UserResourcePermission.user_id.in_(user_ids)
        )

    if not skip_group_perms and not skip_user_perms:
        query = query.union(query2)
    elif skip_group_perms:
        query = query2

    users = [
        PermissionTuple(
            row.User,
            row.perm_name,
            row.type,
            row.Group or None,
            row.Resource,
            False,
            True,
        )
        for row in query
    ]
    return users


def permission_to_04_acls(permissions):
    """
    Legacy acl format kept for bw. compatibility
    :param permissions:
    :return:
    """
    acls = []
    for perm in permissions:
        if perm.type == "user":
            acls.append((perm.user.id, perm.perm_name))
        elif perm.type == "group":
            acls.append(("group:%s" % perm.group.id, perm.perm_name))
    return acls


def permission_to_pyramid_acls(permissions):
    """
    Returns a list of permissions in a format understood by pyramid
    :param permissions:
    :return:
    """
    acls = []
    for perm in permissions:
        if perm.type == "user":
            acls.append((Allow, perm.user.id, perm.perm_name))
        elif perm.type == "group":
            acls.append((Allow, "group:%s" % perm.group.id, perm.perm_name))
    return acls
