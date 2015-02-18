# -*- coding: utf-8 -*-
from __future__ import with_statement
import os
import unittest
import six

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
from ziggurat_foundations.models import ALL_PERMISSIONS, Allow
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from alembic.config import Config
from alembic import command


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


class TestResourceB(Resource):
    __mapper_args__ = {'polymorphic_identity': u'test_resource_b'}

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


def _initTestingDB():
    sql_str = os.environ.get("DB_STRING", 'sqlite://')
    engine = create_engine(sql_str)
    # pyramid way
    maker = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)
    if sql_str.startswith('sqlite'):
        # sqlite will not work with alembic
        Base.metadata.create_all(engine)
    else:
        alembic_cfg = Config()
        alembic_cfg.set_main_option(
            "script_location", "ziggurat_foundations:migrations")
        alembic_cfg.set_main_option("sqlalchemy.url", sql_str)
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

    def _addResourceB(self, resource_id, resource_name=u'test_resource'):
        Resource.__possible_permissions__ = [u'test_perm', u'test_perm1',
                                             u'test_perm2', u'foo_perm',
                                             u'group_perm']
        resource = TestResourceB(resource_id=resource_id,
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

    def test_get_dict_excluded(self):
        created_user = self._addUser()
        dict_ = created_user.get_dict(exclude_keys=['user_name'])
        assert 'user_name' not in dict_

    def test_get_dict_included(self):
        created_user = self._addUser()
        dict_ = created_user.get_dict(include_keys=['user_name'])
        assert ['user_name'] == dict_.keys()

    def test_get_dict_included_excluded(self):
        created_user = self._addUser()
        dict_ = created_user.get_dict(
            include_keys=['user_name', 'id', 'email', 'status'],
            exclude_keys=['email'])
        assert sorted(['user_name', 'id', 'status']) == sorted(dict_.keys())

    def test_appstruct(self):
        created_user = self._addUser()
        appstruct = created_user.get_appstruct()
        self.assertEqual(len(appstruct), 8)

    def test_populate_obj_appstruct(self):
        created_user = self._addUser()
        app_struct = {'user_name': u'new_name'}
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

    def test_by_username_andsecurity_code_existing(self):
        created_user = self._addUser()
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name=u'username',
            security_code=security_code,
            db_session=self.session
        )

        self.assertEqual(created_user, queried_user)

    def test_by_username_andsecurity_code_not_existing(self):
        created_user = self._addUser()
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name=u'not_existing_user',
            security_code=security_code,
            db_session=self.session
        )

        self.assertEqual(queried_user, None)

    def test_by_username_andsecurity_code_wrong_code(self):
        self._addUser()
        queried_user = User.by_user_name_and_security_code(
            user_name=u'username',
            security_code=u'wrong_code',
            db_session=self.session
        )

        self.assertEqual(queried_user, None)

    def test_by_username_andsecurity_code_none(self):
        created_user = self._addUser()
        security_code = created_user.security_code
        User.by_user_name_and_security_code(
            user_name=None,
            security_code=security_code,
            db_session=self.session
        )

        self.assertEqual(None, None)

    def test_by_user_names(self):
        user1 = self._addUser(u'user1', u'email1')
        self._addUser(u'user2', u'email2')
        user3 = self._addUser(u'user3', u'email3')

        queried_users = User.by_user_names([u'user1', u'user3'],
                                           db_session=self.session).all()

        self.assertEqual(len(queried_users), 2)
        self.assertEqual(user1, queried_users[0])
        self.assertEqual(user3, queried_users[1])

    def test_by_user_names_one_none(self):
        user1 = self._addUser(u'user1', u'email1')
        self._addUser(u'user2', u'email2')
        user3 = self._addUser(u'user3', u'email3')

        queried_users = User.by_user_names([u'user1', None, u'user3'],
                                           db_session=self.session).all()

        self.assertEqual(len(queried_users), 2)
        self.assertEqual(user1, queried_users[0])
        self.assertEqual(user3, queried_users[1])

    def test_by_user_names_like(self):
        user1 = self._addUser(u'user1', u'email1')
        self._addUser(u'luser2', u'email2')
        self._addUser(u'noname', u'email3')

        queried_users = User.user_names_like(u'user%',
                                             db_session=self.session).all()
        self.assertEqual(len(queried_users), 1)
        self.assertEqual(user1, queried_users[0])

    def test_by_user_names_like_none(self):

        queried_users = User.user_names_like(None,
                                             db_session=self.session).all()
        self.assertEqual([], queried_users)

    def test_by_email(self):
        created_user = self._addUser()
        queried_user = User.by_email(u'email', db_session=self.session)

        self.assertEqual(created_user, queried_user)

    def test_by_email_none(self):
        self._addUser()
        queried_user = User.by_email(None, db_session=self.session)

        self.assertEqual(None, queried_user)

    def test_by_email_wrong_email(self):
        self._addUser()
        queried_user = User.by_email(u'wrong_email', db_session=self.session)

        self.assertEqual(queried_user, None)

    def test_by_mail_and_username(self):
        created_user = self._addUser()
        queried_user = User.by_email_and_username(u'email', u'username',
                                                  db_session=self.session)

        self.assertEqual(created_user, queried_user)

    def test_by_mail_and_username_wrong_mail(self):
        self._addUser()
        queried_user = User.by_email_and_username(u'wrong_email', u'username',
                                                  db_session=self.session)

        self.assertEqual(queried_user, None)

    def test_by_mail_and_username_wrong_username(self):
        self._addUser()
        queried_user = User.by_email_and_username(u'email', u'wrong_username',
                                                  db_session=self.session)

        self.assertEqual(queried_user, None)

    def test_by_mail_and_username_none(self):
        User.by_email_and_username(u'email', None, db_session=self.session)
        self.assertEqual(None, None)

    def test_gravatar_url(self):
        user = self._addUser()
        user.email = 'arkadiy@bk.ru'
        self.assertEqual(user.gravatar_url(),
                         'https://secure.gravatar.com/avatar/'
                         'cbb6777e4a7ec0d96b33d2033e59fec6?d=mm')

    def test_gravatar_url_with_params(self):
        user = self._addUser()
        user.email = 'arkadiy@bk.ru'
        self.assertEqual(user.gravatar_url(s=100, r='pg'),
                         'https://secure.gravatar.com/avatar/'
                         'cbb6777e4a7ec0d96b33d2033e59fec6?s=100&r=pg&d=mm')

    def test_generate_random_string(self):
        rand_str = User.generate_random_string()

        self.assertEqual(len(rand_str), 7)
        self.assertIsInstance(rand_str, six.string_types)

    def test_generate_random_pass(self):
        rand_str = User.generate_random_pass()

        self.assertEqual(len(rand_str), 7)
        self.assertIsInstance(rand_str, six.string_types)

        rand_str = User.generate_random_pass(20)
        self.assertEqual(len(rand_str), 20)

    def test_regenerate_security_code(self):
        created_user = self._addUser()
        old_code = created_user.security_code
        created_user.regenerate_security_code()
        new_code = created_user.security_code

        self.assertNotEqual(old_code, new_code)
        self.assertEqual(len(new_code), 64)

    def test_user_permissions(self):
        created_user = self._addUser()
        permissions = created_user.permissions
        self.assertEqual(permissions, [(1, u'alter_users'),
                                       (1, u'root')])

    def test_owned_permissions(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        created_user.resources.append(resource)
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      db_session=self.session).all()
        self.assertEqual(resources[0], resource)

    def test_resources_with_perm(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      db_session=self.session).all()
        self.assertEqual(resources[0], resource)

    def test_mixed_perms(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        resource2 = self._addResource(2, u'test_resource')
        created_user.resources.append(resource2)
        resource3 = self._addResource(3, u'test_resource')
        resource4 = self._addResourceB(4, u'test_resource')
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      db_session=self.session).all()
        found_ids = [r.resource_id for r in resources]
        self.assertEqual(sorted(found_ids), [1, 2])

    def test_resources_with_perm_type_found(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      resource_types=['test_resource'],
                                                      db_session=self.session).all()
        self.assertEqual(resources[0], resource)

    def test_resources_with_perm_type_not_found(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      resource_types=['test_resource_b'],
                                                      db_session=self.session).all()
        self.assertEqual(resources, [])

    def test_resources_with_perm_type_other_found(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        resource2 = self._addResourceB(2, u'test_resource')
        resource3 = self._addResource(3, u'test_resource')
        resource4 = self._addResourceB(4, u'test_resource')
        self.session.flush()
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        permission2 = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource2.resource_id)
        resource2.user_permissions.append(permission2)
        permission3 = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource3.resource_id)
        resource3.user_permissions.append(permission3)
        permission4 = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource4.resource_id)
        resource4.user_permissions.append(permission4)
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      resource_types=['test_resource_b'],
                                                      db_session=self.session).all()
        self.assertEqual(len(resources), 2)

    def test_resources_with_wrong_perm(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(
            perm_name=u'test_perm_BAD',
            user_id=created_user.id,
            resource_id=resource.resource_id
        )
        self.assertRaises(AssertionError,
                          lambda: resource.user_permissions.append(permission))

    def test_multiple_resources_with_perm(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id
                                            )
        resource.user_permissions.append(permission)
        resource2 = self._addResource(2, u'test_resource2')
        permission2 = UserResourcePermission(perm_name=u'test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource2.resource_id
                                             )
        resource2.user_permissions.append(permission2)
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      db_session=self.session).all()
        self.assertEqual(resources, [resource, resource2])

    def test_resources_ids_with_perm(self):
        created_user = self._addUser()
        resource1 = self._addResource(1, u'test_resource1')
        resource2 = self._addResource(2, u'test_resource2')
        resource3 = self._addResource(3, u'test_resource3')

        permission1 = UserResourcePermission(perm_name=u'test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource1.resource_id)
        permission2 = UserResourcePermission(perm_name=u'test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource2.resource_id)
        permission3 = UserResourcePermission(perm_name=u'test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource3.resource_id)

        resource1.user_permissions.append(permission1)
        resource2.user_permissions.append(permission2)
        resource3.user_permissions.append(permission3)

        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                                      resource_ids=[1, 3],
                                                      db_session=self.session).all()
        self.assertEqual(resources, [resource1, resource3])

    def test_resources_with_wrong_group_permission(self):

        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        group = self._addGroup()
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
            perm_name=u'test_perm_BAD',
            group_id=group.id,
            resource_id=resource.resource_id
        )
        self.assertRaises(AssertionError,
                          lambda: resource.group_permissions.append(group_permission))

    def test_resources_with_group_permission(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        resource2 = self._addResource(2, u'test_resource2')
        self._addResource(3, u'test_resource3')
        group = self._addGroup()
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
            perm_name=u'test_perm',
            group_id=1,
            resource_id=resource.resource_id
        )
        group_permission2 = GroupResourcePermission(
            perm_name=u'foo_perm',
            group_id=1,
            resource_id=resource2.resource_id
        )
        resource.group_permissions.append(group_permission)
        resource2.group_permissions.append(group_permission2)
        self.session.flush()
        resources = created_user.resources_with_perms([u'foo_perm'],
                                                      db_session=self.session).all()
        self.assertEqual(resources[0], resource2)

    def __set_up_user_group_and_perms(self):
        created_user = self._addUser()
        created_user2 = self._addUser(user_name=u'foouser', email=u'new_email')
        created_user3 = self._addUser(
            user_name=u'foouser2', email=u'new_email2')
        created_user4 = self._addUser(
            user_name=u'foouser3', email=u'new_email3')
        resource = self._addResource(1, u'test_resource')
        group = self._addGroup()
        group2 = self._addGroup(group_name=u'group2')
        group.users.append(created_user)
        group2.users.append(created_user4)
        group_permission = GroupResourcePermission(
            perm_name=u'group_perm',
            group_id=group.id,
            resource_id=resource.resource_id
        )
        group_permission2 = GroupResourcePermission(
            perm_name=u'group_perm',
            group_id=group2.id,
            resource_id=resource.resource_id
        )
        user_permission = UserResourcePermission(
            perm_name=u'test_perm2',
            user_id=created_user.id,
            resource_id=resource.resource_id
        )
        user_permission2 = UserResourcePermission(
            perm_name=u'foo_perm',
            user_id=created_user.id,
            resource_id=resource.resource_id
        )
        user_permission3 = UserResourcePermission(
            perm_name=u'foo_perm',
            user_id=created_user2.id,
            resource_id=resource.resource_id
        )
        user_permission4 = UserResourcePermission(
            perm_name=u'test_perm',
            user_id=created_user3.id,
            resource_id=resource.resource_id
        )
        resource.group_permissions.append(group_permission)
        resource.group_permissions.append(group_permission2)
        resource.user_permissions.append(user_permission)
        resource.user_permissions.append(user_permission2)
        resource.user_permissions.append(user_permission3)
        resource.user_permissions.append(user_permission4)
        self.session.flush()
        self.resource = resource
        self.user = created_user
        self.user2 = created_user2
        self.user3 = created_user3
        self.user4 = created_user4

    def test_resources_with_direct_user_perms(self):
        self.__set_up_user_group_and_perms()
        # test_perm1 from group perms should be ignored
        first = self.resource.direct_perms_for_user(
            self.user, db_session=self.session)
        second = [(1, u'foo_perm'), (1, u'test_perm2')]
        if six.PY2:
            return self.assertItemsEqual(first, second)
        return self.assertCountEqual(first, second)

    def test_resources_with_direct_group_perms(self):
        self.__set_up_user_group_and_perms()
        # test_perm1 from group perms should be ignored
        first = self.resource.group_perms_for_user(
            self.user, db_session=self.session)
        second = [('group:1', u'group_perm')]
        if six.PY2:
            return self.assertItemsEqual(first, second)
        return self.assertCountEqual(first, second)

    def test_resources_with_user_perms(self):
        self.__set_up_user_group_and_perms()
        first = self.resource.perms_for_user(
            self.user, db_session=self.session)
        second = [(1, u'foo_perm'),
                  (u'group:1', u'group_perm'),
                  (1, u'test_perm2')]
        if six.PY2:
            return self.assertItemsEqual(first, second)
        return self.assertCountEqual(first, second)

    def test_users_for_perm(self):
        self.__set_up_user_group_and_perms()
        first = self.resource.users_for_perm(
            u'foo_perm', db_session=self.session)
        second = [(self.user, u'foo_perm',), (self.user2, u'foo_perm',)]
        if six.PY2:
            return self.assertItemsEqual(first, second)
        return self.assertCountEqual(first, second)

    def test_users_for_any_perm(self):
        self.__set_up_user_group_and_perms()
        first = self.resource.users_for_perm(
            '__any_permission__', db_session=self.session)
        second = [
            (self.user, u'group_perm',),
            (self.user, u'test_perm2',),
            (self.user, u'foo_perm',),
            (self.user2, u'foo_perm',),
            (self.user3, u'test_perm',),
            (self.user4, u'group_perm',),
        ]
        if six.PY2:
            return self.assertItemsEqual(first, second)
        return self.assertCountEqual(first, second)


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

    def test_group_repr(self):
        group = self._addGroup()
        self.assertEqual(repr(group), '<Group: group, 1>')

    def test_by_group_name(self):
        added_group = self._addGroup()
        queried_group = Group.by_group_name(u'group',
                                            db_session=self.session)

        self.assertEqual(added_group, queried_group)

    def test_by_group_name_wrong_groupname(self):
        self._addGroup()
        queried_group = Group.by_group_name(u'not existing group',
                                            db_session=self.session)

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

        all_groups = Group.all(db_session=self.session).all()

        self.assertEqual(len(all_groups), 2)
        self.assertEqual(all_groups[0], group1)
        self.assertEqual(all_groups[1], group2)

    def test_user_paginator(self):
        user1 = self._addUser(u'user1', u'email1')
        user2 = self._addUser(u'user2', u'email2')

        group = self._addGroup()
        group.users.append(user1)
        group.users.append(user2)
        users_count = len(group.users)
        get_params = {'foo': 'bar', 'baz': 'xxx'}

        paginator = group.get_user_paginator(1, users_count,
                                             GET_params=get_params)

        self.assertEqual(paginator.page, 1)
        self.assertEqual(paginator.first_item, 1)
        self.assertEqual(paginator.last_item, 2)
        self.assertEqual(paginator.items, [user1, user2])
        self.assertEqual(paginator.item_count, 2)
        self.assertEqual(paginator.page_count, 1)
        self.assertEqual(paginator.kwargs, get_params)

    def test_user_paginator_usernames(self):
        user1 = self._addUser(u'user1', u'email1')
        user2 = self._addUser(u'user2', u'email2')
        user3 = self._addUser(u'user3', u'email3')

        group = self._addGroup()
        group.users.append(user1)
        group.users.append(user2)
        group.users.append(user3)

        # TODO: users count when filtering on names?
        paginator = group.get_user_paginator(1,
                                             user_ids=[1, 3])

        self.assertEqual(paginator.page, 1)
        self.assertEqual(paginator.first_item, 1)
        self.assertEqual(paginator.last_item, 2)
        self.assertEqual(paginator.items, [user1, user3])
        self.assertEqual(paginator.item_count, 2)
        self.assertEqual(paginator.page_count, 1)


class GroupPermissionTestCase(BaseTestCase):

    def test_repr(self):
        group_permission = GroupPermission(group_id=1,
                                           perm_name=u'perm')
        self.assertEqual(repr(group_permission), '<GroupPermission: perm>')

    def test_by_group_and_perm(self):
        self._addGroup()
        queried = GroupPermission.by_group_and_perm(1, u'manage_apps',
                                                    db_session=self.session)
        self.assertEqual(queried.group_id, 1)
        self.assertEqual(queried.perm_name, u'manage_apps')

    def test_by_group_and_perm_wrong_group(self):
        self._addGroup()
        queried = GroupPermission.by_group_and_perm(2,
                                                    u'manage_apps', db_session=self.session)
        self.assertEqual(queried, None)

    def test_by_group_and_perm_wrong_perm(self):
        self._addGroup()
        queried = GroupPermission.by_group_and_perm(1, u'wrong_perm',
                                                    db_session=self.session)
        self.assertEqual(queried, None)


class UserPermissionTestCase(BaseTestCase):

    def test_repr(self):
        user_permission = UserPermission(user_id=1, perm_name=u'perm')
        self.assertEqual(repr(user_permission), '<UserPermission: perm>')

    def test_by_user_and_perm(self):
        self._addUser()
        user_permission = UserPermission.by_user_and_perm(1, u'root',
                                                          db_session=self.session)

        self.assertEqual(user_permission.user_id, 1)
        self.assertEqual(user_permission.perm_name, u'root')

    def test_by_user_and_perm_wrong_username(self):
        self._addUser()
        user_permission = UserPermission.by_user_and_perm(999, u'root',
                                                          db_session=self.session)

        self.assertEqual(user_permission, None)

    def test_by_user_and_perm_wrong_permname(self):
        self._addUser()
        user_permission = UserPermission.by_user_and_perm(1, u'wrong',
                                                          db_session=self.session)

        self.assertEqual(user_permission, None)


class UserGroupTestCase(BaseTestCase):

    def test_repr(self):
        user_group = UserGroup(user_id=1, group_id=1)
        self.assertEqual(repr(user_group), '<UserGroup: g:1, u:1>')


class GroupResourcePermissionTestCase(BaseTestCase):

    def test_repr(self):
        group_resource_perm = GroupResourcePermission(group_id=1,
                                                      resource_id=1,
                                                      perm_name='perm')
        self.assertEqual(repr(group_resource_perm),
                         '<GroupResourcePermission: g:1, perm, r:1>')


class AddResourceTestCase(BaseTestCase):

    def test_pkey(self):
        resource = self._addResource(99, 'some random name')
        self.assertEqual(resource.resource_id, 99)

    def test_nopkey(self):
        resource = self._addResource(None, 'some random name')
        self.assertEqual(resource.resource_id, 1)

if __name__ == '__main__':
    unittest.main()  # pragma: nocover
