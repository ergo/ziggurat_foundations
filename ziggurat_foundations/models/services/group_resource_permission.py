# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services import BaseService

__all__ = ["GroupResourcePermissionService"]


class GroupResourcePermissionService(BaseService):
    @classmethod
    def get(cls, group_id, resource_id, perm_name, db_session=None):
        """
        Fetch row using primary key -
        will use existing object in session if already present

        :param group_id:
        :param resource_id:
        :param perm_name:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        return db_session.query(cls.model).get([group_id, resource_id, perm_name])
