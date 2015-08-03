class BaseService(object):
    model = None
    model_proxy = None

    @classmethod
    def all(cls, db_session=None):
        return cls.model.base_query(db_session)
