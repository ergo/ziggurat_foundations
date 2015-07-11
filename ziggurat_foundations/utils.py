"""
Utility functions.
"""

import sqlalchemy as sa

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


def get_db_session(session=None, obj=None):
    """ utility function that attempts to return sqlalchemy session that could
    have been created/passed in one of few ways:

    * It first tries to read session attached to instance
      if object argument was passed

    * then it tries to return  session passed as argument

    * finally tries to read pylons-like threadlocal called DBSession

    * if this fails exception is thrown """
    # try to read the session from instance
    from ziggurat_foundations import models
    if obj:
        return sa.orm.session.object_session(obj)
    # try passed session
    elif session:
        return session
    # try global pylons-like session then
    elif models.DBSession:
        return models.DBSession
    raise Exception('No Session found')