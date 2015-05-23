"""
Utility functions.
"""

from cryptacular.core import PasswordChecker
from ziggurat_foundations.models import Allow


class PlaceholderPasswordChecker(PasswordChecker):
    """Match and return false on check() for '*' (a password hash
    consisting of a single asterisk.) DelegatingPasswordManager would
    otherwise throw an exception 'unrecognized password hash'.
    """

    def match(self, encoded):
        return encoded == '*'

    def check(self, encoded, password):
        return False


def permission_to_04_acls(permissions):
    acls = []
    for perm in permissions:
        if perm.type == 'user':
            acls.append((perm.user.id, perm.perm_name))
        elif perm.type == 'group':
            acls.append(('group:%s' % perm.group.id, perm.perm_name))
    return acls


def permission_to_pyramid_acls(permissions):
    acls = []
    for perm in permissions:
        if perm.type == 'user':
            acls.append((Allow, perm.user.id, perm.perm_name))
        elif perm.type == 'group':
            acls.append((Allow, 'group:%s' % perm.group.id, perm.perm_name))
    return acls