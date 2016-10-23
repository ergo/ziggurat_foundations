from __future__ import unicode_literals
from . import BaseService
from ..base import get_db_session


class UserResourcePermissionService(BaseService):
    @classmethod
    def get(cls, user_id, resource_id, perm_name, db_session=None):
        db_session = get_db_session(db_session)
        lvars = locals()
        pkey = [lvars[c.name] for c in cls.model.get_primary_key()]
        return db_session.query(cls.model).get(pkey)

    @classmethod
    def by_resource_user_and_perm(cls, user_id, perm_name, resource_id,
                                  db_session=None):
        """ return all instances by user name, perm name and resource id """
        db_session = get_db_session(db_session)

        query = db_session.query(cls.model).filter(
            cls.model.user_id == user_id)
        query = query.filter(cls.model.resource_id == resource_id)
        query = query.filter(cls.model.perm_name == perm_name)
        return query.first()
