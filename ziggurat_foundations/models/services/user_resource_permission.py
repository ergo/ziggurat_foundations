from __future__ import unicode_literals
from ziggurat_foundations.models.services import BaseService
from ziggurat_foundations.models.base import get_db_session

__all__ = ['UserResourcePermissionService']


class UserResourcePermissionService(BaseService):
    @classmethod
    def get(cls, user_id, resource_id, perm_name, db_session=None):
        db_session = get_db_session(db_session)
        return db_session.query(cls.model).get(
            [user_id, resource_id, perm_name])

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
