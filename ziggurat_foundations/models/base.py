# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlalchemy as sa

from ziggurat_foundations.exc import ZigguratSessionException


class BaseModel(object):
    """ Basic class that all other classes inherit from that supplies some
    basic methods useful for interaction with packages like:
    deform, colander or wtforms """

    @classmethod
    def _get_keys(cls):
        """ returns column names for this model """
        return sa.orm.class_mapper(cls).c.keys()

    @classmethod
    def get_primary_key(cls):
        return sa.orm.class_mapper(cls).primary_key

    def get_dict(self, exclude_keys=None, include_keys=None):
        """
        return dictionary of keys and values corresponding to this model's
        data - if include_keys is null the function will return all keys

        :param exclude_keys: (optional) is a list of columns from model that
        should not be returned by this function
        :param include_keys: (optional) is a list of columns from model that
        should be returned by this function
        :return:
        """
        d = {}
        exclude_keys_list = exclude_keys or []
        include_keys_list = include_keys or []
        for k in self._get_keys():
            if k not in exclude_keys_list and (
                k in include_keys_list or not include_keys
            ):
                d[k] = getattr(self, k)
        return d

    def get_appstruct(self):
        """ return list of tuples keys and values corresponding to this model's
        data """
        result = []
        for k in self._get_keys():
            result.append((k, getattr(self, k)))
        return result

    def populate_obj(self, appstruct, exclude_keys=None, include_keys=None):
        """
        updates instance properties *for column names that exist*
        for this model and are keys present in passed dictionary

        :param appstruct: (dictionary)
        :param exclude_keys: (optional) is a list of columns from model that
        should not be updated by this function
        :param include_keys: (optional) is a list of columns from model that
        should be updated by this function
        :return:
        """
        exclude_keys_list = exclude_keys or []
        include_keys_list = include_keys or []
        for k in self._get_keys():
            if (
                k in appstruct
                and k not in exclude_keys_list
                and (k in include_keys_list or not include_keys)
            ):
                setattr(self, k, appstruct[k])

    def populate_obj_from_obj(self, instance, exclude_keys=None, include_keys=None):
        """
        updates instance properties *for column names that exist*
        for this model and are properties present in passed dictionary

        :param instance:
        :param exclude_keys: (optional) is a list of columns from model that
        should not be updated by this function
        :param include_keys: (optional) is a list of columns from model that
        should be updated by this function
        :return:
        """
        exclude_keys_list = exclude_keys or []
        include_keys_list = include_keys or []
        for k in self._get_keys():
            if (
                hasattr(instance, k)
                and k not in exclude_keys_list
                and (k in include_keys_list or not include_keys)
            ):
                setattr(self, k, getattr(instance, k))

    def get_db_session(self, session=None):
        """
        Attempts to return session via get_db_session utility function
        :meth:`~ziggurat_foundations.models.get_db_session`

        :param session:
        :return:
        """
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
        """
        Deletes the object via session, this will permanently delete the
        object from storage on commit

        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session, self)
        db_session.delete(self)

def get_db_session(session=None, obj=None):
    """
    utility function that attempts to return sqlalchemy session that could
    have been created/passed in one of few ways:

    * It first tries to read session attached to instance
      if object argument was passed

    * then it tries to return  session passed as argument

    * finally tries to read pylons-like threadlocal called DBSession

    * if this fails exception is thrown

    :param session:
    :param obj:
    :return:
    """
    # try to read the session from instance
    from ziggurat_foundations import models

    if obj:
        return sa.orm.session.object_session(obj)
    # try passed session
    elif session:
        return session
    # try global pylons-like session then
    elif models.DBSession:
        return models.DBSession
    raise ZigguratSessionException("No Session found")
