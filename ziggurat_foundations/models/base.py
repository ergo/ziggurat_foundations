import sqlalchemy as sa
from ziggurat_foundations.utils import get_db_session

class BaseModel(object):
    """ Basic class that all other classes inherit from that supplies some
    basic methods useful for interaction with packages like:
    deform, colander or wtforms """

    @classmethod
    def _get_keys(cls):
        """ returns column names for this model """
        return sa.orm.class_mapper(cls).c.keys()

    def get_dict(self, exclude_keys=None, include_keys=None):
        """ return dictionary of keys and values corresponding to this model's
        data
        if include_keys is null the function will return all keys

        ::arg include_keys (optional) is a list of columns from model that
        should be returned by this function
        ::arg exclude_keys (optional) is a list of columns from model that
        should not be returned by this function
        """
        d = {}
        exclude_keys_list = exclude_keys or []
        include_keys_list = include_keys or []
        for k in self._get_keys():
            if k not in exclude_keys_list and \
                    (k in include_keys_list or not include_keys):
                d[k] = getattr(self, k)
        return d

    def get_appstruct(self):
        """ return list of tuples keys and values corresponding to this model's
        data """
        l = []
        for k in self._get_keys():
            l.append((k, getattr(self, k),))
        return l

    def populate_obj(self, appstruct):
        """ updates instance properties with dictionary values *for keys that
        exist* for this model """
        for k in self._get_keys():
            if k in appstruct:
                setattr(self, k, appstruct[k])

    def get_db_session(self, session=None):
        """ Attempts to return session via get_db_session utility function
        :meth:`~ziggurat_foundations.models.get_db_session`"""
        return get_db_session(session, self)

    def persist(self, flush=False, db_session=None):
        """
        Adds object to session, if the object was freshly created this will
        persist the object in the storage on commit

        :param flush: boolean - if true then the session will be flushed
        instantly
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        db_session.add(self)
        if flush:
            db_session.flush()

    def delete(self, db_session=None):
        """ Deletes the object via session, this will permanently delete the
        object from storage on commit """
        db_session = get_db_session(db_session, self)
        db_session.delete(self)

    @classmethod
    def base_query(cls, db_session=None):
        """
        Returns a base query object one can use to search on simple properties
        :param db_session:
        :return:
        """
        return get_db_session(db_session).query(cls)