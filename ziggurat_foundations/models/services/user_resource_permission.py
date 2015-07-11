from . import ModelManager
from ...utils import get_db_session


class UserResourcePermissionManager(ModelManager):
    @classmethod
    def by_resource_user_and_perm(cls, user_id, perm_name, resource_id,
                                  db_session=None):
        """ return all instances by user name, perm name and resource id """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.user_id == user_id)
        query = query.filter(cls.resource_id == resource_id)
        query = query.filter(cls.perm_name == perm_name)
        return query.first()


        # @classmethod
        # def allowed_permissions(cls, key):
        #        """ ensures we can only use permission that can be assigned
        #            to this resource type"""
        #        if key in cls.__possible_permissions__:
        #            return key
        #        raise KeyError