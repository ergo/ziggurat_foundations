from . import ModelManager
from ...utils import get_db_session


class ExternalIdentityManager(ModelManager):
    @classmethod
    def by_external_id_and_provider(cls, external_id, provider_name,
                                    db_session=None):
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(cls.external_id == external_id)
        query = query.filter(cls.provider_name == provider_name)
        return query.first()

    @classmethod
    def user_by_external_id_and_provider(cls, external_id, provider_name,
                                         db_session=None):
        db_session = get_db_session(db_session)
        query = db_session.query(cls._ziggurat_models.User)
        query = query.filter(cls.external_id == external_id)
        query = query.filter(cls._ziggurat_models.User.user_name == cls.local_user_name)
        query = query.filter(cls.provider_name == provider_name)
        return query.first()
