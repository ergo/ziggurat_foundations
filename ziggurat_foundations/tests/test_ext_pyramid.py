# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

import pytest

from ziggurat_foundations.tests import BaseTestCase, add_user


class TestExtPyramidLogin(BaseTestCase):
    def test_logon_bad(self, pyramid_app):
        result = pyramid_app.get("/sign_in").json
        assert result["view"] == "bad_auth"
        result = pyramid_app.post(
            "/sign_in", params={"login": "foo", "password": "bar"}
        ).json
        assert result["view"] == "bad_auth"

    def test_logon_good(self, db_session, pyramid_app):
        for item in (
            {"user_name": "username1", "email": "email", "password": "pass1"},
            {"user_name": "username2", "email": "email2", "password": "pass2"},
        ):
            user = add_user(db_session, **item)
            db_session.add(user)
            db_session.flush()
        result = pyramid_app.post(
            "/sign_in", params={"login": "username1", "password": "pass1"}
        ).json
        assert result["view"] == "sign_in"
        assert result["username"] == "username1"

    @pytest.mark.parametrize(
        "username,password", [("username1", "BAD"), ("username", "password")]
    )
    def test_logon_bad_pass(self, db_session, pyramid_app, username, password):
        user = add_user(db_session, user_name="username1", email="email")
        db_session.add(user)
        db_session.flush()
        result = pyramid_app.post(
            "/sign_in", params={"login": username, "password": password}
        ).json
        assert result["view"] == "bad_auth"

    def test_index_unlogged(self, db_session, pyramid_app):
        result = pyramid_app.post("/").json
        assert result["view"] == "index"
        assert result["username"] is None

    def test_index_logged(self, db_session, pyramid_app):
        user = add_user(db_session, user_name="username1", email="email")
        db_session.add(user)
        db_session.flush()
        result = pyramid_app.post(
            "/sign_in", params={"login": "username1", "password": "password"}
        )
        result = pyramid_app.post("/", headers=result.headers).json
        assert result["view"] == "index"
        assert result["username"] == "username1"
