import sqlalchemy as sa
from collections import namedtuple
from .utils import get_db_session

try:
    from pyramid.security import Allow, Deny, ALL_PERMISSIONS


except ImportError as e:
    Allow = 'Allow'
    Deny = 'Deny'
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

class ANY_PERMISSION_CLS(object):
    def __eq__(self, other):
        return '__any_permission__' == other

    def __ne__(self, other):
        return '__any_permission__' != other


ANY_PERMISSION = ANY_PERMISSION_CLS()


PermissionTuple = namedtuple('PermissionTuple',
                             ['user', 'perm_name', 'type', 'group', 'resource',
                              'owner', 'allowed'])


def resource_permissions_for_users(model, perm_names, resource_ids=None,
                                   user_ids=None, group_ids=None,
                                   resource_types=None,
                                   limit_group_permissions=False,
                                   skip_user_perms=False,
                                   skip_group_perms=False,
                                   db_session=None):
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
    db_session = get_db_session(db_session, model)
    query = db_session.query(model._ziggurat_models.GroupResourcePermission.perm_name,
                             model._ziggurat_models.User,
                             model._ziggurat_models.Group,
                             sa.literal('group').label('type'),
                             model._ziggurat_models.Resource
    )
    if limit_group_permissions:
        query = query.outerjoin(model._ziggurat_models.User, model._ziggurat_models.User.id == None)
    else:
        query = query.filter(model._ziggurat_models.User.id == model._ziggurat_models.UserGroup.user_id)

    query = query.filter(
        model._ziggurat_models.Resource.resource_id == model._ziggurat_models.GroupResourcePermission.resource_id)
    query = query.filter(
        model._ziggurat_models.Group.id == model._ziggurat_models.GroupResourcePermission.group_id)
    if resource_ids:
        query = query.filter(
            model._ziggurat_models.GroupResourcePermission.resource_id.in_(resource_ids))
    if resource_types:
        query = query.filter(model._ziggurat_models.Resource.resource_type.in_(resource_types))
    query = query.filter(model._ziggurat_models.UserGroup.group_id ==
                         model._ziggurat_models.GroupResourcePermission.group_id)
    if (perm_names not in ([ANY_PERMISSION], ANY_PERMISSION) and perm_names):
        query = query.filter(
            model._ziggurat_models.GroupResourcePermission.perm_name.in_(perm_names))
    if group_ids:
        query = query.filter(
            model._ziggurat_models.GroupResourcePermission.group_id.in_(group_ids))
    if user_ids:
        query = query.filter(
            model._ziggurat_models.UserGroup.user_id.in_(user_ids))
    query2 = db_session.query(model._ziggurat_models.UserResourcePermission.perm_name,
                              model._ziggurat_models.User,
                              model._ziggurat_models.Group,
                              sa.literal('user').label('type'),
                              model._ziggurat_models.Resource)
    # group needs to be present to work for union, but never actually matched
    query2 = query2.outerjoin(model._ziggurat_models.Group, model._ziggurat_models.Group.id == None)
    query2 = query2.filter(model._ziggurat_models.User.id ==
                           model._ziggurat_models.UserResourcePermission.user_id)
    query2 = query2.filter(
        model._ziggurat_models.Resource.resource_id == model._ziggurat_models.UserResourcePermission.resource_id)
    if (perm_names not in ([ANY_PERMISSION], ANY_PERMISSION) and perm_names):
        query2 = query2.filter(
            model._ziggurat_models.UserResourcePermission.perm_name.in_(perm_names))
    if resource_ids:
        query2 = query2.filter(
            model._ziggurat_models.UserResourcePermission.resource_id.in_(resource_ids))
    if resource_types:
        query2 = query2.filter(model._ziggurat_models.Resource.resource_type.in_(resource_types))
    if user_ids:
        query2 = query2.filter(
            model._ziggurat_models.UserResourcePermission.user_id.in_(user_ids))

    if not skip_group_perms and not skip_user_perms:
        query = query.union(query2)
    elif skip_group_perms:
        query = query2

    users = [PermissionTuple(row.User, row.perm_name, row.type,
                             row.Group or None, row.Resource, False, True)
             for row in query]
    return users