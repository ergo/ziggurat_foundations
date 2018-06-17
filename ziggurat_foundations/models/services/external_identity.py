# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services import BaseService

__all__ = ["ExternalIdentityService"]


class ExternalIdentityService(BaseService):
    @classmethod
    def get(cls, external_id, local_user_id, provider_name, db_session=None):
        """
        Fetch row using primary key -
        will use existing object in session if already present

        :param external_id:
        :param local_user_id:
        :param provider_name:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return db_session.query(cls.model).get(
            [external_id, local_user_id, provider_name]
        )

    @classmethod
    def by_external_id_and_provider(cls, external_id, provider_name, db_session=None):
        """
        Returns ExternalIdentity instance based on search params

        :param external_id:
        :param provider_name:
        :param db_session:
        :return: ExternalIdentity
        """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model)
        query = query.filter(cls.model.external_id == external_id)
        query = query.filter(cls.model.provider_name == provider_name)
        return query.first()

    @classmethod
    def user_by_external_id_and_provider(
        cls, external_id, provider_name, db_session=None
    ):
        """
        Returns User instance based on search params

        :param external_id:
        :param provider_name:
        :param db_session:
        :return: User
        """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.models_proxy.User)
        query = query.filter(cls.model.external_id == external_id)
        query = query.filter(cls.model.provider_name == provider_name)
        query = query.filter(cls.models_proxy.User.id == cls.model.local_user_id)
        return query.first()
