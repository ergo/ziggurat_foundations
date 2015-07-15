from . import ModelManager
from ...utils import get_db_session


class ExternalIdentityService(ModelManager):

    @classmethod
    def by_external_id_and_provider(cls, external_id, provider_name,
                                    db_session=None):

        print(cls.__dict__)
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model)
        query = query.filter(cls.model.external_id == external_id)
        query = query.filter(cls.model.provider_name == provider_name)
        return query.first()

    @classmethod
    def user_by_external_id_and_provider(cls, external_id, provider_name,
                                         db_session=None):
        db_session = get_db_session(db_session)
        query = db_session.query(cls.models_proxy.User)
        query = query.filter(cls.model.external_id == external_id)
        query = query.filter(cls.model.provider_name == provider_name)
        query = query.filter(cls.models_proxy.User.user_name == cls.model.local_user_name)
        return query.first()
