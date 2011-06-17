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

    def _addUser(self, user_name=u'username', email=u'email'):
        user = User(user_name=user_name, email=email, status=0)
        user.set_password('password')
        self.session.add(user)
        self.session.flush()
        return user

    def _addGroup(self, group_name=u'group', description=u'desc'):
        group = Group(
            group_name=group_name,
            description=description
        )
        self.session.add(group)
        self.session.flush()
        return group


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

    def test_by_user_name_existing(self):
        created_user = self._addUser()
        queried_user = User.by_user_name('username')

        self.assertEqual(created_user, queried_user)

    def test_by_user_name_not_existing(self):
        self._addUser()
        queried_user = User.by_user_name('not_existing_user')

        self.assertEqual(queried_user, None)

    def test_by_username_andsecurity_code_existing(self):
        created_user = self._addUser()
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name='username', 
            security_code=security_code
        )

        self.assertEqual(created_user, queried_user)

    def test_by_username_andsecurity_code_not_existing(self):
        created_user = self._addUser()
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name='not_existing_user', 
            security_code=security_code
        )

        self.assertEqual(queried_user, None)

    def test_by_username_andsecurity_code_wrong_code(self):
        self._addUser()
        queried_user = User.by_user_name_and_security_code(
            user_name='username', 
            security_code='wrong_code'
        )

        self.assertEqual(queried_user, None)

    def test_by_user_names(self):
        user1 = self._addUser(u'user1', u'email1')
        user2 = self._addUser(u'user2', u'email2')
        user3 = self._addUser(u'user3', u'email3')

        queried_users = User.by_user_names([u'user1', u'user3']).all()

        self.assertEqual(len(queried_users), 2)
        self.assertEqual(user1, queried_users[0])
        self.assertEqual(user3, queried_users[1])

    def test_by_user_names_like(self):
        user1 = self._addUser(u'user1', u'email1')
        self._addUser(u'luser2', u'email2')
        self._addUser(u'noname', u'email3')

        queried_users = User.user_names_like(u'user%').all()
        self.assertEqual(len(queried_users), 1)
        self.assertEqual(user1, queried_users[0])

    def test_by_email(self):
        created_user = self._addUser()
        queried_user = User.by_email(u'email')

        self.assertEqual(created_user, queried_user)

    def test_by_email_wrong_email(self):
        self._addUser()
        queried_user = User.by_email(u'wrong_email')

        self.assertEqual(queried_user, None)

    def test_by_mail_and_username(self):
        created_user = self._addUser()
        queried_user = User.by_email_and_username(u'email', 'username')

        self.assertEqual(created_user, queried_user)

    def test_by_mail_and_username_wrong_mail(self):
        self._addUser()
        queried_user = User.by_email_and_username(u'wrong_email', 'username')

        self.assertEqual(queried_user, None)

    def test_by_mail_and_username_wrong_username(self):
        self._addUser()
        queried_user = User.by_email_and_username(u'email', 'wrong_username')

        self.assertEqual(queried_user, None)

    def test_gravatar_url(self):
        user = self._addUser()
        self.assertEqual(user.gravatar_url(), 
                         'https://secure.gravatar.com/avatar/'
                         '0c83f57c786a0b4a39efab23731c7ebc?d=mm')
        
    def test_generate_random_string(self):
        rand_str = User.generate_random_string()
        
        self.assertEqual(len(rand_str), 7)
        self.assertIsInstance(rand_str, unicode)
        
    def test_generate_random_pass(self):
        rand_str = User.generate_random_pass()
        
        self.assertEqual(len(rand_str), 7)
        self.assertIsInstance(rand_str, unicode)
        
        rand_str = User.generate_random_pass(20)
        self.assertEqual(len(rand_str), 20)
        
    def regenerate_security_code(self):
        user = self._addUser()
        old_code = user.security_code
        new_code = user.regenerate_security_code()
        
        self.assertNotEqual(old_code, new_code)
        self.assertEqual(len(new_code), 32)

class GroupTestCase(BaseTestCase):
    def test_add_group(self):
        group = Group(
            group_name=u'example group',
            description=u'example description'
        )
        self.session.add(group)
        self.session.flush()

        group = self.session.query(Group)
        group = group.filter(Group.group_name == u'example group').first()
        
        self.assertEqual(group.group_name, u'example group')
        self.assertEqual(group.description, u'example description')
        self.assertEqual(group.member_count, 0)

    def test_by_group_name(self):
        added_group = self._addGroup()
        queried_group = Group.by_group_name(u'group')

        self.assertEqual(added_group, queried_group)

    def test_by_group_name_wrong_groupname(self):
        self._addGroup()
        queried_group = Group.by_group_name(u'not existing group')

        self.assertEqual(queried_group, None)

    def test_users(self):
        user1 = self._addUser(u'user1', u'email1')
        user2 = self._addUser(u'user2', u'email2')

        group = self._addGroup()
        group.users.append(user1)
        group.users.append(user2)

        self.assertEqual(group.users[0], user1)
        self.assertEqual(group.users[1], user2)


    def test_users_dynamic(self):
        user1 = self._addUser(u'user1', u'email1')
        user2 = self._addUser(u'user2', u'email2')

        group = self._addGroup()
        group.users.append(user1)
        group.users.append(user2)
        group_users = group.users_dynamic.all()

        self.assertEqual(group_users[0], user1)
        self.assertEqual(group_users[1], user2)

    def test_all(self):
        group1 = self._addGroup(u'group1')
        group2 = self._addGroup(u'group2')

        all_groups = Group.all().all()

        self.assertEqual(len(all_groups), 2)
        self.assertEqual(all_groups[0], group1)
        self.assertEqual(all_groups[1], group2)

