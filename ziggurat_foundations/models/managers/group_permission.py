from . import ModelManager
from ...utils import get_db_session


class GroupPermissionManager(ModelManager):
    @classmethod
    def by_group_and_perm(cls, group_id, perm_name, db_session=None):
        """" return by by_user_and_perm and permission name """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.group_id == group_id)
        query = query.filter(cls.perm_name == perm_name)
        return query.first()