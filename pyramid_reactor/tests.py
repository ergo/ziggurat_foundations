# -*- coding: utf-8 -*-
import unittest

from sqlalchemy.ext.declarative import declarative_base

from pyramid_reactor.models import UserMixin
from pyramid_reactor.models import GroupMixin
from pyramid_reactor.models import GroupPermissionMixin
from pyramid_reactor.models import UserPermissionMixin
from pyramid_reactor.models import UserGroupMixin
from pyramid_reactor.models import UserResourcePermissionMixin
from pyramid_reactor.models import GroupResourcePermissionMixin
from pyramid_reactor.models import ResourceMixin


Base = declarative_base()


class User(UserMixin, Base):
    __tablename__ = 'users'


class GroupPermission(GroupPermissionMixin, Base):
    __tablename__ = 'groups_permissions'


class UserGroup(UserGroupMixin, Base):
    __tablename__ = 'users_groups'


class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    __tablename__ = 'groups_resources_permissions'


class Resource(ResourceMixin, Base):
    __tablename__ = 'resources'


class UserPermission(UserPermissionMixin, Base):
    __tablename__ = 'users_permissions'


class UserResourcePermission(UserResourcePermissionMixin, Base):
    __tablename__ = 'users_resources_permissions'


def _initTestingDB():
    from sqlalchemy.orm import scoped_session
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    DBSession = scoped_session()
    dbsession = DBSession()
    dbsession.configure(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return dbsession


class UserTestCase(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()

