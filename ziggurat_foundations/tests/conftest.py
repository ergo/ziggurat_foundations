# -*- coding: utf-8 -*-
from __future__ import absolute_import, unicode_literals

import os

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from ziggurat_foundations import ziggurat_model_init
from ziggurat_foundations.models.external_identity import ExternalIdentityMixin
from ziggurat_foundations.models.group import GroupMixin
from ziggurat_foundations.models.group_permission import GroupPermissionMixin
from ziggurat_foundations.models.group_resource_permission import (
    GroupResourcePermissionMixin,
)
from ziggurat_foundations.models.resource import ResourceMixin
from ziggurat_foundations.models.user import UserMixin
from ziggurat_foundations.models.user_group import UserGroupMixin
from ziggurat_foundations.models.user_permission import UserPermissionMixin
from ziggurat_foundations.models.user_resource_permission import (
    UserResourcePermissionMixin,
)
from ziggurat_foundations.permissions import ALL_PERMISSIONS, Allow

not_postgres = "postgres" not in os.environ.get("DB_STRING", "").lower()

Base = declarative_base()


class Group(GroupMixin, Base):
    __possible_permissions__ = (
        "root_administration",
        "administration",
        "backend_admin_panel",
        "manage_apps",
    )


class GroupPermission(GroupPermissionMixin, Base):
    pass


class UserGroup(UserGroupMixin, Base):
    pass


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass


class Resource(ResourceMixin, Base):
    def __acl__(self):
        acls = []

        if self.owner_user_id:
            acls.extend([(Allow, self.owner_user_id, ALL_PERMISSIONS)])

        if self.owner_group_id:
            acls.extend([(Allow, "group:%s" % self.owner_group_id, ALL_PERMISSIONS)])
        return acls


class ResourceTestObj(Resource):
    __mapper_args__ = {"polymorphic_identity": "test_resource"}


class ResourceTestobjB(Resource):
    __mapper_args__ = {"polymorphic_identity": "test_resource_b"}


class UserPermission(UserPermissionMixin, Base):
    pass


class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass


class ExternalIdentity(ExternalIdentityMixin, Base):
    pass


class User(UserMixin, Base):
    __possible_permissions__ = ["root", "alter_users", "custom1"]


ziggurat_model_init(
    User,
    Group,
    UserGroup,
    GroupPermission,
    UserPermission,
    UserResourcePermission,
    GroupResourcePermission,
    Resource,
    ExternalIdentity,
)


@pytest.fixture
def db_session(request):
    sql_str = os.environ.get("DB_STRING", "sqlite://")
    engine = create_engine(sql_str)
    engine.echo = True
    # pyramid way
    maker = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)
    engine.execute("DROP TABLE IF EXISTS alembic_ziggurat_foundations_version")
    if sql_str.startswith("sqlite"):
        # sqlite will not work with alembic
        Base.metadata.create_all(engine)
    else:
        alembic_cfg = Config()
        alembic_cfg.set_main_option(
            "script_location", "ziggurat_foundations:migrations"
        )
        alembic_cfg.set_main_option("sqlalchemy.url", sql_str)
        command.upgrade(alembic_cfg, "head")

    session = maker()

    def teardown():
        session.rollback()
        session.close()

    request.addfinalizer(teardown)

    return session


@pytest.fixture
def db_session2(request):
    sql_str = os.environ.get("DB_STRING2", "sqlite://")
    engine = create_engine(sql_str)
    engine.echo = True
    # pyramid way
    maker = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)
    engine.execute("DROP TABLE IF EXISTS alembic_ziggurat_foundations_version")
    if sql_str.startswith("sqlite"):
        # sqlite will not work with alembic
        Base.metadata.create_all(engine)
    else:
        alembic_cfg = Config()
        alembic_cfg.set_main_option(
            "script_location", "ziggurat_foundations:migrations"
        )
        alembic_cfg.set_main_option("sqlalchemy.url", sql_str)
        command.upgrade(alembic_cfg, "head")

    session = maker()

    def teardown():
        session.rollback()
        session.close()

    request.addfinalizer(teardown)

    return session


@pytest.fixture
def pyramid_app(request, db_session):
    from webtest import TestApp
    from pyramid.authentication import AuthTktAuthenticationPolicy
    from pyramid.authorization import ACLAuthorizationPolicy
    from pyramid.config import Configurator
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInSuccess
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInBadAuth
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignOut

    auth_policy = AuthTktAuthenticationPolicy("secret")
    authorization_policy = ACLAuthorizationPolicy()

    settings = {"ziggurat_foundations.session_provider_callable": lambda x: db_session}

    config = Configurator(
        settings=settings,
        authentication_policy=auth_policy,
        authorization_policy=authorization_policy,
    )
    config.include("pyramid_jinja2")
    config.include("ziggurat_foundations.ext.pyramid.get_user")
    config.include("ziggurat_foundations.ext.pyramid.sign_in")

    # add ziggurat context handlers
    def sign_in(req):
        user = req.context.user
        for h in req.context.headers:
            req.response.headers.add(h[0], value=h[1])
        return {"view": "sign_in", "username": user.user_name, "user_id": user.id}

    def sign_out(req):
        return {"view": "sign_out"}

    def bad_auth(req):
        return {"view": "bad_auth"}

    def index(req):
        username = None
        if req.user:
            username = req.user.user_name
        return {"view": "index", "username": username}

    config.add_view(sign_in, context=ZigguratSignInSuccess, renderer="json")
    config.add_view(sign_out, context=ZigguratSignOut, renderer="json")
    config.add_view(bad_auth, context=ZigguratSignInBadAuth, renderer="json")
    config.add_route("/", "/")
    config.add_view(index, route_name="/", renderer="json")
    return TestApp(config.make_wsgi_app())
