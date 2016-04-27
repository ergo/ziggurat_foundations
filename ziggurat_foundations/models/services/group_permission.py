from __future__ import unicode_literals
from . import BaseService
from ..base import get_db_session


class GroupPermissionService(BaseService):
    @classmethod
    def by_group_and_perm(cls, group_id, perm_name, db_session=None):
        """" return by by_user_and_perm and permission name """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model).filter(
            cls.model.group_id == group_id)
        query = query.filter(cls.model.perm_name == perm_name)
        return query.first()
