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


class TestResource(Resource):
    __mapper_args__ = {"polymorphic_identity": "test_resource"}


class TestResourceB(Resource):
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
