from collections import namedtuple

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