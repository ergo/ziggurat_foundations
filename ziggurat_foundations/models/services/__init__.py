# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ziggurat_foundations.models.base import get_db_session


class BaseService(object):
    model = None
    models_proxy = None

    @classmethod
    def all(cls, klass, db_session=None):
        """
        returns all objects of specific type - will work correctly with
        sqlalchemy inheritance models, you should normally use models
        base_query()  instead of this function its for bw. compat purposes

        :param klass:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return db_session.query(klass)

    @classmethod
    def base_query(cls, db_session=None):
        """
        returns base query for specific service

        :param db_session:
        :return: query
        """
        db_session = get_db_session(db_session)
        return db_session.query(cls.model)
