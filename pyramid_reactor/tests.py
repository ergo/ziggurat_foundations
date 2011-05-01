# -*- coding: utf-8 -*-
import unittest

from sqlalchemy.ext.declarative import declarative_base

import pyramid_reactor
from pyramid_reactor.models import UserMixin
from pyramid_reactor.models import GroupMixin
from pyramid_reactor.models import GroupPermissionMixin
from pyramid_reactor.models import UserPermissionMixin
from pyramid_reactor.models import UserGroupMixin
from pyramid_reactor.models import UserResourcePermissionMixin
from pyramid_reactor.models import GroupResourcePermissionMixin
from pyramid_reactor.models import ResourceMixin


Base = declarative_base()

class Group(GroupMixin, Base):
    __tablename__ = 'groups'
pyramid_reactor.models.Group = Group

class GroupPermission(GroupPermissionMixin, Base):
    __tablename__ = 'groups_permissions'
pyramid_reactor.models.GroupPermission = GroupPermission

class UserGroup(UserGroupMixin, Base):
    __tablename__ = 'users_groups'
pyramid_reactor.models.UserGroup = UserGroup

class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    __tablename__ = 'groups_resources_permissions'
pyramid_reactor.models.GroupResourcePermission = GroupResourcePermission

class Resource(ResourceMixin, Base):
    __tablename__ = 'resources'
pyramid_reactor.models.Resource = Resource

class UserPermission(UserPermissionMixin, Base):
    __tablename__ = 'users_permissions'
pyramid_reactor.models.UserPermission = UserPermission

class UserResourcePermission(UserResourcePermissionMixin, Base):
    __tablename__ = 'users_resources_permissions'
pyramid_reactor.models.UserResourcePermission = UserResourcePermission
        
class User(UserMixin, Base):
    __tablename__ = 'users'
pyramid_reactor.models.User = User


def _initTestingDB():
    from sqlalchemy.orm import scoped_session, sessionmaker
    from sqlalchemy import create_engine
    engine = create_engine('sqlite://')
    DBSession = scoped_session(sessionmaker())
    dbsession = DBSession()
    dbsession.configure(bind=engine)
    pyramid_reactor.models.DBSession = DBSession
    Base.metadata.bind = engine
    Base.metadata.create_all(engine)
    return dbsession


class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()

    def _addUser(self, user_name=u'username'):
        user = User(user_name=user_name, email=u'email', status=0)
        user.set_password('password')
        self.session.add(user)
        self.session.flush()
        return user


class UserTestCase(BaseTestCase):

    def test_add_user(self):
        user = User(user_name=u'username', email=u'email', status=0)
        self.session.add(user)
        self.session.flush()

        user = self.session.query(User).filter(User.user_name == u'username')
        user = user.first()
        self.assertEqual(user.user_name, u'username')
        self.assertEqual(user.email, u'email')
        self.assertEqual(user.status, 0)

    def test_by_user_name(self):
        created_user = user = self._addUser()
        queried_user = User.by_user_name('username')

        self.assertEqual(created_user, queried_user)

    def test_gravatar_url(self):
        user = self._addUser()
        self.assertEqual(user.gravatar_url(), 
                         'https://secure.gravatar.com/avatar/'
                         '0c83f57c786a0b4a39efab23731c7ebc?d=mm')
