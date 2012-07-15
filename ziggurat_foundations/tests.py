# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import unittest

from sqlalchemy.ext.declarative import declarative_base
from ziggurat_foundations.models import UserMixin
from ziggurat_foundations.models import GroupMixin
from ziggurat_foundations.models import GroupPermissionMixin
from ziggurat_foundations.models import UserPermissionMixin
from ziggurat_foundations.models import UserGroupMixin
from ziggurat_foundations.models import UserResourcePermissionMixin
from ziggurat_foundations.models import GroupResourcePermissionMixin
from ziggurat_foundations.models import ResourceMixin, ExternalIdentityMixin
from ziggurat_foundations import ziggurat_model_init
from ziggurat_foundations.models import ALL_PERMISSIONS
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from alembic.config import Config
from alembic.script import ScriptDirectory
from alembic.migration import MigrationContext


Base = declarative_base()

class Group(GroupMixin, Base):
    __possible_permissions__ = ('root_administration',
                                'administration',
                                'backend_admin_panel',
                                'manage_apps',)

class GroupPermission(GroupPermissionMixin, Base):
    pass

class UserGroup(UserGroupMixin, Base):
    pass

class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass

class Resource(ResourceMixin, Base):
    def __acl__(self):
        return []
        acls = [(Allow, 'group:1', ALL_PERMISSIONS,), ]

        if self.owner_user_id:
            acls.extend([(Allow, self.owner_user_id, ALL_PERMISSIONS,), ])

        if self.owner_group_id:
            acls.extend([(Allow, "group:%s" % self.owner_group_id,
                          ALL_PERMISSIONS,), ])
        return acls

class TestResource(Resource):
    __mapper_args__ = {'polymorphic_identity': u'test_resource'}

class UserPermission(UserPermissionMixin, Base):
    pass

class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass

class ExternalIdentity(ExternalIdentityMixin, Base):
    pass

class User(UserMixin, Base):
    pass

ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource,
                   ExternalIdentity)

import time

def _initTestingDB():
    sql_str = os.environ.get("DB_STRING", 'sqlite://')
    engine = create_engine(sql_str)
    # pyramid way
    maker = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)
    connection = engine.connect()
    if sql_str.startswith('sqlite'):
        # sqlite will not work with alembic 
        Base.metadata.create_all(engine)
    else:
        alembic_cfg = Config()
        alembic_cfg.set_main_option("script_location", "ziggurat_foundations:migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", sql_str)
        from alembic import command
        command.stamp(alembic_cfg, None)
        command.upgrade(alembic_cfg, "head")
    return maker()

    # pylons/akhet monkeypatching way
#    import ziggurat_foundations
#    DBSession = scoped_session(sessionmaker())
#    dbsession = DBSession()
#    dbsession.configure(bind=engine)
#    ziggurat_foundations.models.DBSession = DBSession
#    Base.metadata.bind = engine
#    Base.metadata.create_all(engine)
#    return dbsession




class BaseTestCase(unittest.TestCase):
    def setUp(self):
        self.session = _initTestingDB()
        
        
    def tearDown(self):
        self.session.commit()
        self.session.close()

    def _addUser(self, user_name=u'username', email=u'email'):
        user = User(user_name=user_name, email=email, status=0)
        user.set_password('password')
        root_perm = UserPermission(perm_name=u'root')
        users_perm = UserPermission(perm_name=u'alter_users')
        user.user_permissions.append(root_perm)
        user.user_permissions.append(users_perm)
        self.session.add(user)
        self.session.flush()
        return user

    def _addResource(self, resource_id, resource_name=u'test_resource'):
        Resource.__possible_permissions__ = [u'test_perm', u'test_perm1',
                                             u'test_perm2', u'foo_perm',
                                             u'group_perm']
        resource = TestResource(resource_id=resource_id,
                            resource_name=resource_name)
        self.session.add(resource)
        self.session.flush()
        return resource

    def _addGroup(self, group_name=u'group', description=u'desc'):
        group = Group(
            group_name=group_name,
            description=description
        )
        test_perm = GroupPermission(perm_name=u'manage_apps')
        group.permissions.append(test_perm)
        self.session.add(group)
        self.session.flush()
        return group

    def assertIsInstance(self, obj, cls, msg=None):
        """
        For python 2.6 compat.
        """
        _MAX_LENGTH = 80
        def safe_repr(obj, short=False):
            try:
                result = repr(obj)
            except Exception:
                result = object.__repr__(obj)
            if not short or len(result) < _MAX_LENGTH:
                return result
            return result[:_MAX_LENGTH] + ' [truncated]...'
        if not isinstance(obj, cls):
            standardMsg = '%s is not an instance of %r' % (safe_repr(obj), cls)
            self.fail(self._formatMessage(msg, standardMsg))


class ModelTestCase(BaseTestCase):

    def test_get_keys(self):
        keys = User._get_keys()
        self.assertEqual(len(keys), 8)

    def test_get_dict(self):
        created_user = self._addUser()
        dict_ = created_user.get_dict()
        self.assertEqual(len(dict_), 8)

    def test_appstruct(self):
        created_user = self._addUser()
        appstruct = created_user.get_appstruct()
        self.assertEqual(len(appstruct), 8)

    def test_populate_obj_appstruct(self):
        created_user = self._addUser()
        app_struct = {'user_name':u'new_name'}
        created_user.populate_obj(app_struct)
        self.assertEqual(created_user.user_name, u'new_name')

#    def test_session(self):
#        session = get_db_session(None, self._addUser())
#        from sqlalchemy.orm import ScopedSession
#        self.assertIsInstance(session, ScopedSession)

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

    def test_delete_user(self):
        self._addUser()
        to_delete = User.by_user_name(u'username', db_session=self.session)
        self.session.delete(to_delete)
        self.session.commit()

    def test_user_repr(self):
        user = self._addUser()
        self.assertEqual(repr(user), '<User: username>')

    def test_check_password_correct(self):
        user = self._addUser()
        self.assertTrue(user.check_password(u'password'))

    def test_check_password_wrong(self):
        user = self._addUser()
        self.assertFalse(user.check_password(u'wrong_password'))

    def test_by_user_name_existing(self):
        created_user = self._addUser()
        queried_user = User.by_user_name(u'username', db_session=self.session)

        self.assertEqual(created_user, queried_user)

    def test_by_user_name_not_existing(self):
        self._addUser()
        queried_user = User.by_user_name(u'not_existing_user',
                                         db_session=self.session)

        self.assertEqual(queried_user, None)

    def test_by_user_name_none(self):
        queried_user = User.by_user_name(None, db_session=self.session)

        self.assertEqual(None, queried_user)

':
    unittest.main()  # pragma: nocover
