# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

import os

import pytest

from ziggurat_foundations.models.services import BaseService
from ziggurat_foundations.tests import BaseTestCase
from ziggurat_foundations.tests.conftest import User

not_multi_db = os.environ.get("DB_STRING", "") == os.environ.get("DB_STRING2", "")


def add_user(i, db_name, db_session):
    user = User(
        id=i,
        user_name="username_{}_db_{}".format(i, db_name),
        email="email_{}".format(i),
        status=0,
    )
    db_session.add(user)


@pytest.mark.skipif(not_multi_db, reason="requires different db strings")
class TestMultiDB(BaseTestCase):
    def test_users_in_two_databases(self, db_session, db_session2):
        for x in range(1, 5):
            add_user(x, "a", db_session=db_session)
        for x in range(1, 3):
            add_user(x, "b", db_session=db_session2)
        db_session.flush()
        db_session2.flush()

        db_users = BaseService.all(User, db_session=db_session).all()
        db2_users = BaseService.all(User, db_session=db_session2).all()
        assert len(db_users) == 4
        assert len(db2_users) == 2
        assert db_users[0].user_name == "username_1_db_a"
        assert db2_users[0].user_name == "username_1_db_b"
