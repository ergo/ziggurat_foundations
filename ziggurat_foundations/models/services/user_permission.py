from __future__ import unicode_literals
from . import BaseService
from ..base import get_db_session


class UserPermissionService(BaseService):
    @classmethod
    def by_user_and_perm(cls, user_id, perm_name, db_session=None):
        """ return by user and permission name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model).filter(
            cls.model.user_id == user_id)
        query = query.filter(cls.model.perm_name == perm_name)
        return query.first()
