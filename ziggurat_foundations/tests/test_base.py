# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.tests import add_user, BaseTestCase, DummyUserObj
from ziggurat_foundations.tests.conftest import User
from ziggurat_foundations.models.services.user import UserService


class TestModel(BaseTestCase):
    def test_get_keys(self, db_session):
        keys = User._get_keys()
        assert len(keys) == 9

    def test_get_dict(self, db_session):
        created_user = add_user(db_session)
        dict_ = created_user.get_dict()
        assert len(dict_) == 9

    def test_get_dict_excluded(self, db_session):
        created_user = add_user(db_session)
        dict_ = created_user.get_dict(exclude_keys=["user_name"])
        assert "user_name" not in dict_

    def test_get_dict_included(self, db_session):
        created_user = add_user(db_session)
        dict_ = created_user.get_dict(include_keys=["user_name"])
        assert ["user_name"] == list(dict_.keys())

    def test_get_dict_included_excluded(self, db_session):
        created_user = add_user(db_session)
        dict_ = created_user.get_dict(
            include_keys=["user_name", "id", "email", "status"], exclude_keys=["email"]
        )
        assert sorted(["user_name", "id", "status"]) == sorted(dict_.keys())

    def test_appstruct(self, db_session):
        created_user = add_user(db_session)
        appstruct = created_user.get_appstruct()
        assert len(appstruct) == 9

    def test_populate_obj_appstruct(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        app_struct = {
            "user_name": "new_name",
            "user_password": "foo",
            "email": "change@email.com",
        }
        created_user.populate_obj(app_struct)
        assert created_user.user_name == app_struct["user_name"]
        assert created_user.user_password == app_struct["user_password"]
        assert created_user.email == app_struct["email"]

    def test_populate_obj_appstruct_exclude(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        app_struct = {
            "user_name": "new_name",
            "user_password": "foo",
            "email": "change@email.com",
        }
        created_user.populate_obj(app_struct, exclude_keys=["user_password"])
        assert created_user.user_name == app_struct["user_name"]
        assert created_user.user_password is None
        assert created_user.email == app_struct["email"]

    def test_populate_obj_appstruct_include(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        app_struct = {
            "user_name": "new_name",
            "user_password": "foo",
            "email": "change@email.com",
        }
        created_user.populate_obj(app_struct, include_keys=["user_password"])
        assert created_user.user_name != app_struct["user_name"]
        assert created_user.user_password == app_struct["user_password"]
        assert created_user.email != app_struct["email"]

    def test_populate_obj_obj(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        test_obj = DummyUserObj()
        created_user.populate_obj_from_obj(test_obj)
        assert created_user.user_name == test_obj.user_name
        assert created_user.user_password == test_obj.user_password
        assert created_user.email == test_obj.email

    def test_populate_obj_obj_exclude(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        test_obj = DummyUserObj()
        created_user.populate_obj_from_obj(test_obj, exclude_keys=["user_password"])
        assert created_user.user_name == test_obj.user_name
        assert created_user.user_password is None
        assert created_user.email == test_obj.email

    def test_populate_obj_obj_include(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        test_obj = DummyUserObj()
        created_user.populate_obj_from_obj(test_obj, include_keys=["user_password"])
        assert created_user.user_name != test_obj.user_name
        assert created_user.user_password == test_obj.user_password
        assert created_user.email != test_obj.email

    def test_session(self, db_session):
        from sqlalchemy.orm.session import Session

        session = get_db_session(None, add_user(db_session))
        assert isinstance(session, Session)

    def test_add_object_without_flush(self, db_session):
        user = User(user_name="some_new_user", email="foo")
        assert user.id is None
        user.persist(db_session=db_session)
        assert user.id is None

    def test_add_object_with_flush(self, db_session):
        user = User(user_name="some_new_user", email="foo")
        assert user.id is None
        user.persist(flush=True, db_session=db_session)
        assert user.id is not None

    def test_delete_object_with_flush(self, db_session):
        user = User(user_name="some_new_user", email="foo")
        assert user.id is None
        user.persist(flush=True, db_session=db_session)
        assert user.id is not None
        uid = user.id
        UserService.by_id(uid, db_session=db_session) is not None
        user.delete()
        assert UserService.by_id(uid, db_session=db_session) is None


class TestMigrations(BaseTestCase):
    def test_migrations(self, db_session):
        pass
