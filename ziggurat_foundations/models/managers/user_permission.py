from . import ModelManager
from ...utils import get_db_session


class UserPermissionManager(ModelManager):
    @classmethod
    def by_user_and_perm(cls, user_id, perm_name, db_session=None):
        """ return by user and permission name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.user_id == user_id)
        query = query.filter(cls.perm_name == perm_name)
        return query.first()