# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals
import logging
import os
import six
import pytest

from sqlalchemy.ext.declarative import declarative_base
from . import ziggurat_model_init
from .permissions import PermissionTuple, ALL_PERMISSIONS, Allow
from .models.user import UserMixin
from .models.group import GroupMixin
from .models.group_permission import GroupPermissionMixin
from .models.user_permission import UserPermissionMixin
from .models.user_group import UserGroupMixin
from .models.user_resource_permission import UserResourcePermissionMixin
from .models.group_resource_permission import GroupResourcePermissionMixin
from .models.resource import ResourceMixin
from .models.external_identity import ExternalIdentityMixin
from .models.services.external_identity import ExternalIdentityService
from .models.base import get_db_session

# from .utils import permission_to_04_acls, permission_to_pyramid_acls

from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

from alembic.config import Config
from alembic import command

logging.basicConfig()

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
        acls = []

        if self.owner_user_id:
            acls.extend([(Allow, self.owner_user_id, ALL_PERMISSIONS,), ])

        if self.owner_group_id:
            acls.extend([(Allow, "group:%s" % self.owner_group_id,
                          ALL_PERMISSIONS,), ])
        return acls


class TestResource(Resource):
    __mapper_args__ = {'polymorphic_identity': 'test_resource'}


class TestResourceB(Resource):
    __mapper_args__ = {'polymorphic_identity': 'test_resource_b'}


class UserPermission(UserPermissionMixin, Base):
    pass


class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass


class ExternalIdentity(ExternalIdentityMixin, Base):
    pass


class User(UserMixin, Base):
    __possible_permissions__ = ['root', 'alter_users', 'custom1']


ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                    UserResourcePermission, GroupResourcePermission, Resource,
                    ExternalIdentity)

@pytest.fixture
def db_session(request):
    sql_str = os.environ.get("DB_STRING", 'sqlite://',)
    engine = create_engine(sql_str)
    # pyramid way
    maker = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)
    engine.execute(
        'DROP TABLE IF EXISTS alembic_ziggurat_foundations_version')
    if sql_str.startswith('sqlite'):
        # sqlite will not work with alembic
        Base.metadata.create_all(engine)
    else:
        alembic_cfg = Config()
        alembic_cfg.set_main_option('script_location',
                                    'ziggurat_foundations:migrations')
        alembic_cfg.set_main_option('sqlalchemy.url', sql_str)
        command.upgrade(alembic_cfg, "head")

    session = maker()

    def teardown():
        session.rollback()
        session.close()

    request.addfinalizer(teardown)

    return session


def check_one_in_other(first, second):
    while first:
        item = first.pop()
        ix = second.index(item)
        second.pop(ix)
    assert len(first) == len(second)


def add_user(db_session, user_name='username', email='email',
             perms=['root', 'alter_users']):
    user = User(user_name=user_name, email=email, status=0)
    user.set_password('password')
    for perm in perms:
        u_perm = UserPermission(perm_name=perm)
        user.user_permissions.append(u_perm)
    db_session.add(user)
    db_session.flush()
    return user


def add_resource(db_session, resource_id, resource_name='test_resource'):
    Resource.__possible_permissions__ = [
        'test_perm', 'test_perm1',
        'test_perm2', 'foo_perm',
        'group_perm', 'group_perm2']
    resource = TestResource(resource_id=resource_id,
                            resource_name=resource_name)
    db_session.add(resource)
    db_session.flush()
    return resource


def add_resource_b(db_session, resource_id, resource_name='test_resource'):
    Resource.__possible_permissions__ = ['test_perm', 'test_perm1',
                                         'test_perm2', 'foo_perm',
                                         'group_perm', 'group_perm2']
    resource = TestResourceB(resource_id=resource_id,
                             resource_name=resource_name)
    db_session.add(resource)
    db_session.flush()
    return resource


def add_group(db_session, group_name='group', description='desc'):
    group = Group(
        group_name=group_name,
        description=description
    )
    test_perm = GroupPermission(perm_name='manage_apps')
    group.permissions.append(test_perm)
    db_session.add(group)
    db_session.flush()
    return group



class BaseTestCase(object):

    def set_up_user_group_and_perms(self, db_session):
        """
        perm map:

        username:
            first_user : root, alter_users
            res_perms: r1:g1:foo_perm, r1:g1:test_perm2

        foouser:
            user_perms : custom
            res_perms: r2:foo_perm

        baruser:
            user_perms : root, alter_users
            res_perms: r2:test_perm

        bazuser:
            user_perms : root, alter_users
            res_perms: r1:g2:group_perm

        """
        created_user = add_user(db_session,user_name="first_user")
        created_user2 = add_user(db_session,user_name='foouser', email='new_email',
                                      perms=['custom'])
        created_user3 = add_user(db_session,
            user_name='baruser', email='new_email2')
        created_user4 = add_user(db_session,
            user_name='bazuser', email='new_email3')
        resource = add_resource(db_session,1, 'test_resource')
        resource2 = add_resource_b(db_session,2, 'other_resource')
        group = add_group(db_session,)
        group2 = add_group(db_session,group_name='group2')
        group.users.append(created_user)
        group2.users.append(created_user4)
        group_permission = GroupResourcePermission(
            perm_name='group_perm',
            group_id=group.id,
        )
        group_permission2 = GroupResourcePermission(
            perm_name='group_perm',
            group_id=group2.id,
        )
        user_permission = UserResourcePermission(
            perm_name='test_perm2',
            user_id=created_user.id,
        )
        user_permission2 = UserResourcePermission(
            perm_name='foo_perm',
            user_id=created_user.id,
        )
        user2_permission = UserResourcePermission(
            perm_name='foo_perm',
            user_id=created_user2.id,
        )
        user3_permission = UserResourcePermission(
            perm_name='test_perm',
            user_id=created_user3.id,
        )
        resource.group_permissions.append(group_permission)
        resource.group_permissions.append(group_permission2)
        resource.user_permissions.append(user_permission)
        resource.user_permissions.append(user_permission2)
        resource2.user_permissions.append(user2_permission)
        resource2.user_permissions.append(user3_permission)
        db_session.flush()
        self.resource = resource
        self.resource2 = resource2
        self.user = created_user
        self.user2 = created_user2
        self.user3 = created_user3
        self.user4 = created_user4
        self.group = group
        self.group2 = group2


class DummyUserObj(object):
    def __init__(self):
        self.user_name = 'new_name'
        self.user_password = 'foo'
        self.email = 'change@email.com'


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
        dict_ = created_user.get_dict(exclude_keys=['user_name'])
        assert 'user_name' not in dict_

    def test_get_dict_included(self, db_session):
        created_user = add_user(db_session)
        dict_ = created_user.get_dict(include_keys=['user_name'])
        assert ['user_name'] == list(dict_.keys())

    def test_get_dict_included_excluded(self, db_session):
        created_user = add_user(db_session)
        dict_ = created_user.get_dict(
            include_keys=['user_name', 'id', 'email', 'status'],
            exclude_keys=['email'])
        assert sorted(['user_name', 'id', 'status']) == sorted(dict_.keys())

    def test_appstruct(self, db_session):
        created_user = add_user(db_session)
        appstruct = created_user.get_appstruct()
        assert len(appstruct) == 9

    def test_populate_obj_appstruct(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        app_struct = {'user_name': 'new_name',
                      'user_password': 'foo',
                      'email': 'change@email.com'}
        created_user.populate_obj(app_struct)
        assert created_user.user_name == app_struct['user_name']
        assert created_user.user_password == app_struct['user_password']
        assert created_user.email == app_struct['email']

    def test_populate_obj_appstruct_exclude(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        app_struct = {'user_name': 'new_name',
                      'user_password': 'foo',
                      'email': 'change@email.com'}
        created_user.populate_obj(app_struct,
                                  exclude_keys=['user_password'])
        assert created_user.user_name == app_struct['user_name']
        assert created_user.user_password == None
        assert created_user.email == app_struct['email']

    def test_populate_obj_appstruct_include(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        app_struct = {'user_name': 'new_name',
                      'user_password': 'foo',
                      'email': 'change@email.com'}
        created_user.populate_obj(app_struct,
                                  include_keys=['user_password'])
        assert created_user.user_name != app_struct['user_name']
        assert created_user.user_password == app_struct['user_password']
        assert created_user.email != app_struct['email']

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
        created_user.populate_obj_from_obj(test_obj,
                                           exclude_keys=['user_password'])
        assert created_user.user_name == test_obj.user_name
        assert created_user.user_password == None
        assert created_user.email == test_obj.email

    def test_populate_obj_obj_include(self, db_session):
        created_user = add_user(db_session)
        # reset password
        created_user.user_password = None
        test_obj = DummyUserObj()
        created_user.populate_obj_from_obj(test_obj,
                                           include_keys=['user_password'])
        assert created_user.user_name != test_obj.user_name
        assert created_user.user_password == test_obj.user_password
        assert created_user.email != test_obj.email

    def test_session(self, db_session):
        from sqlalchemy.orm.session import Session
        session = get_db_session(None, add_user(db_session))
        assert isinstance(session, Session)

    def test_add_object_without_flush(self, db_session):
        user = User(user_name='some_new_user', email='foo')
        assert user.id is None
        user.persist(db_session=db_session)
        assert user.id is None

    def test_add_object_with_flush(self, db_session):
        user = User(user_name='some_new_user', email='foo')
        assert user.id is None
        user.persist(flush=True, db_session=db_session)
        assert user.id is not None

    def test_delete_object_with_flush(self, db_session):
        user = User(user_name='some_new_user', email='foo')
        assert user.id is None
        user.persist(flush=True, db_session=db_session)
        assert user.id is not None
        uid = user.id
        User.by_id(uid, db_session=db_session) is not None
        user.delete()
        assert User.by_id(uid, db_session=db_session) is None


class TestMigrations(BaseTestCase):
    def test_migrations(self, db_session):
        pass


class TestUser(BaseTestCase):
    def test_add_user(self, db_session):
        user = User(user_name='username', email='email', status=0)
        db_session.add(user)
        db_session.flush()

        user = db_session.query(User).filter(User.user_name == 'username')
        user = user.first()
        assert user.user_name == 'username'
        assert user.email == 'email'
        assert user.status == 0

    def test_delete_user(self, db_session):
        add_user(db_session)
        to_delete = User.by_user_name('username', db_session=db_session)
        db_session.delete(to_delete)
        db_session.commit()

    def test_user_repr(self, db_session):
        user = add_user(db_session)
        assert repr(user) == '<User: username>'

    def test_check_password_correct(self, db_session):
        user = add_user(db_session)
        assert user.check_password('password') is True

    def test_check_password_wrong(self, db_session):
        user = add_user(db_session)
        assert user.check_password('wrong_password') is False

    def test_by_user_name_existing(self, db_session):
        created_user = add_user(db_session)
        queried_user = User.by_user_name('username', db_session=db_session)

        assert created_user == queried_user

    def test_by_user_name_not_existing(self, db_session):
        add_user(db_session)
        queried_user = User.by_user_name('not_existing_user',
                                         db_session=db_session)

        assert queried_user is None

    def test_by_user_name_none(self, db_session):
        queried_user = User.by_user_name(None, db_session=db_session)

        assert queried_user is None

    def test_by_username_andsecurity_code_existing(self, db_session):
        created_user = add_user(db_session)
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name='username',
            security_code=security_code,
            db_session=db_session
        )

        assert created_user == queried_user

    def test_by_username_andsecurity_code_not_existing(self, db_session):
        created_user = add_user(db_session)
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name='not_existing_user',
            security_code=security_code,
            db_session=db_session
        )

        assert queried_user is None

    def test_by_username_andsecurity_code_wrong_code(self, db_session):
        add_user(db_session)
        queried_user = User.by_user_name_and_security_code(
            user_name='username',
            security_code='wrong_code',
            db_session=db_session
        )

        assert queried_user is None

    def test_by_username_andsecurity_code_none(self, db_session):
        created_user = add_user(db_session)
        security_code = created_user.security_code
        found = User.by_user_name_and_security_code(
            user_name=None,
            security_code=security_code,
            db_session=db_session
        )

        assert found is None

    def test_by_user_names(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        add_user(db_session,'user2', 'email2')
        user3 = add_user(db_session,'user3', 'email3')

        queried_users = User.by_user_names(['user1', 'user3'],
                                           db_session=db_session).all()

        assert len(queried_users) == 2
        assert user1 == queried_users[0]
        assert user3 == queried_users[1]

    def test_by_user_names_one_none(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        add_user(db_session,'user2', 'email2')
        user3 = add_user(db_session,'user3', 'email3')

        queried_users = User.by_user_names(['user1', None, 'user3'],
                                           db_session=db_session).all()

        assert len(queried_users) == 2
        assert user1 == queried_users[0]
        assert user3 == queried_users[1]

    def test_by_user_names_like(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        add_user(db_session,'luser2', 'email2')
        add_user(db_session,'noname', 'email3')

        queried_users = User.user_names_like('user%',
                                             db_session=db_session).all()
        assert len(queried_users) == 1
        assert user1 == queried_users[0]

    def test_by_user_names_like_none(self, db_session):
        queried_users = User.user_names_like(None,
                                             db_session=db_session).all()
        assert [] == queried_users

    def test_by_email(self, db_session):
        created_user = add_user(db_session)
        queried_user = User.by_email('email', db_session=db_session)

        assert created_user == queried_user

    def test_by_email_none(self, db_session):
        add_user(db_session)
        queried_user = User.by_email(None, db_session=db_session)

        assert queried_user is None

    def test_by_email_wrong_email(self, db_session):
        add_user(db_session)
        queried_user = User.by_email('wrong_email', db_session=db_session)

        assert queried_user is None

    def test_by_mail_and_username(self, db_session):
        created_user = add_user(db_session)
        queried_user = User.by_email_and_username('email', 'username',
                                                  db_session=db_session)

        assert created_user == queried_user

    def test_by_mail_and_username_wrong_mail(self, db_session):
        add_user(db_session)
        queried_user = User.by_email_and_username('wrong_email', 'username',
                                                  db_session=db_session)

        assert queried_user is None

    def test_by_mail_and_username_wrong_username(self, db_session):
        add_user(db_session)
        queried_user = User.by_email_and_username('email', 'wrong_username',
                                                  db_session=db_session)

        assert queried_user is None

    def test_by_mail_and_username_none(self, db_session):
        found = User.by_email_and_username('email', None,
                                           db_session=db_session)
        assert found is None

    def test_gravatar_url(self, db_session):
        user = add_user(db_session)
        user.email = 'arkadiy@bk.ru'
        assert user.gravatar_url() == 'https://secure.gravatar.com/avatar/' \
                                      'cbb6777e4a7ec0d96b33d2033e59fec6?d=mm'

    def test_gravatar_url_with_params(self, db_session):
        import six.moves.urllib.parse as parser
        user = add_user(db_session)
        user.email = 'arkadiy@bk.r'
        gravatar_url = user.gravatar_url(s=100, r='pg')
        parsed_url = parser.urlparse(gravatar_url)
        qs_dict = parser.parse_qs(parsed_url.query)
        assert qs_dict == {'s': ['100'], 'd': ['mm'], 'r': ['pg']}

    def test_generate_random_string(self, db_session):
        rand_str = User.generate_random_string()

        assert len(rand_str) == 7
        assert isinstance(rand_str, six.string_types)

    def test_generate_random_pass(self, db_session):
        rand_str = User.generate_random_pass()

        assert len(rand_str) == 7
        assert isinstance(rand_str, six.string_types)

        rand_str = User.generate_random_pass(20)
        assert len(rand_str) == 20

    def test_regenerate_security_code(self, db_session):
        created_user = add_user(db_session)
        old_code = created_user.security_code
        created_user.regenerate_security_code()
        new_code = created_user.security_code

        assert old_code != new_code
        assert len(new_code) == 64


class TestUserPermissionse(BaseTestCase):
    def test_user_permissions(self, db_session):
        created_user = add_user(db_session)
        permissions = created_user.permissions
        expected = [
            PermissionTuple(created_user, 'alter_users', 'user', None, None,
                            False, True),
            PermissionTuple(created_user, 'root', 'user', None, None, False,
                            True)]
        check_one_in_other(permissions, expected)

    def test_owned_permissions(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        created_user.resources.append(resource)
        db_session.flush()
        resources = created_user.resources_with_perms(
            ['test_perm'], db_session=db_session).all()
        assert resources[0] == resource

    def test_resources_with_perm(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        permission = UserResourcePermission(
            perm_name='test_perm', user_id=created_user.id,
            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        db_session.flush()
        resources = created_user.resources_with_perms(['test_perm'],
                                                      db_session=db_session).all()
        assert resources[0] == resource

    def test_mixed_perms(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        permission = UserResourcePermission(
            perm_name='test_perm', user_id=created_user.id,
            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        resource2 = add_resource(db_session,2, 'test_resource')
        created_user.resources.append(resource2)
        resource3 = add_resource(db_session,3, 'test_resource')
        resource4 = add_resource_b(db_session,4, 'test_resource')
        db_session.flush()
        resources = created_user.resources_with_perms(['test_perm'],
                                                      db_session=db_session).all()
        found_ids = [r.resource_id for r in resources]
        assert sorted(found_ids) == [1, 2]

    def test_resources_with_perm_type_found(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        permission = UserResourcePermission(perm_name='test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        db_session.flush()
        resources = created_user.resources_with_perms(['test_perm'],
                                                      resource_types=[
                                                          'test_resource'],
                                                      db_session=db_session).all()
        assert resources[0] == resource

    def test_resources_with_perm_type_not_found(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        permission = UserResourcePermission(perm_name='test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        db_session.flush()
        resources = created_user.resources_with_perms(['test_perm'],
                                                      resource_types=[
                                                          'test_resource_b'],
                                                      db_session=db_session).all()
        assert resources == []

    def test_resources_with_perm_type_other_found(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        resource2 = add_resource_b(db_session,2, 'test_resource')
        resource3 = add_resource(db_session,3, 'test_resource')
        resource4 = add_resource_b(db_session,4, 'test_resource')
        db_session.flush()
        permission = UserResourcePermission(perm_name='test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        permission2 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource2.resource_id)
        resource2.user_permissions.append(permission2)
        permission3 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource3.resource_id)
        resource3.user_permissions.append(permission3)
        permission4 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource4.resource_id)
        resource4.user_permissions.append(permission4)
        db_session.flush()
        resources = created_user.resources_with_perms(['test_perm'],
                                                      resource_types=[
                                                          'test_resource_b'],
                                                      db_session=db_session).all()
        assert len(resources) == 2

    def test_resources_with_wrong_perm(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        permission = UserResourcePermission(
            perm_name='test_perm_bad',
            user_id=created_user.id,
            resource_id=resource.resource_id
        )
        with pytest.raises(AssertionError):
            resource.user_permissions.append(permission)

    def test_multiple_resources_with_perm(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        permission = UserResourcePermission(perm_name='test_perm',
                                            user_id=created_user.id,
                                            resource_id=resource.resource_id
                                            )
        resource.user_permissions.append(permission)
        resource2 = add_resource(db_session,2, 'test_resource2')
        permission2 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource2.resource_id
                                             )
        resource2.user_permissions.append(permission2)
        resources = created_user.resources_with_perms(['test_perm'],
                                                      db_session=db_session).all()
        assert resources == [resource, resource2]

    def test_resources_ids_with_perm(self, db_session):
        created_user = add_user(db_session)
        resource1 = add_resource(db_session,1, 'test_resource1')
        resource2 = add_resource(db_session,2, 'test_resource2')
        resource3 = add_resource(db_session,3, 'test_resource3')

        permission1 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource1.resource_id)
        permission2 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource2.resource_id)
        permission3 = UserResourcePermission(perm_name='test_perm',
                                             user_id=created_user.id,
                                             resource_id=resource3.resource_id)

        resource1.user_permissions.append(permission1)
        resource2.user_permissions.append(permission2)
        resource3.user_permissions.append(permission3)

        db_session.flush()
        resources = created_user.resources_with_perms(['test_perm'],
                                                      resource_ids=[1, 3],
                                                      db_session=db_session).all()
        assert resources == [resource1, resource3]

    def test_resources_with_wrong_group_permission(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        group = add_group(db_session,)
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
            perm_name='test_perm_bad',
            group_id=group.id,
            resource_id=resource.resource_id
        )
        with pytest.raises(AssertionError):
            resource.group_permissions.append(group_permission)

    def test_resources_with_group_permission(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session,1, 'test_resource')
        resource2 = add_resource(db_session,2, 'test_resource2')
        add_resource(db_session,3, 'test_resource3')
        group = add_group(db_session,)
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
            perm_name='test_perm',
            group_id=1,
            resource_id=resource.resource_id
        )
        group_permission2 = GroupResourcePermission(
            perm_name='foo_perm',
            group_id=1,
            resource_id=resource2.resource_id
        )
        resource.group_permissions.append(group_permission)
        resource2.group_permissions.append(group_permission2)
        db_session.flush()
        resources = created_user.resources_with_perms(['foo_perm'],
                                                      db_session=db_session).all()
        assert resources[0] == resource2

    def test_resources_with_direct_user_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        # test_perm1 from group perms should be ignored
        perms = self.resource.direct_perms_for_user(
            self.user, db_session=db_session)
        second = [PermissionTuple(self.user, 'foo_perm', 'user', None,
                                  self.resource, False, True),
                  PermissionTuple(self.user, 'test_perm2', 'user', None,
                                  self.resource, False, True)]

        check_one_in_other(perms, second)

    def test_resources_with_direct_group_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        # test_perm1 from group perms should be ignored
        perms = self.resource.group_perms_for_user(
            self.user, db_session=db_session)
        second = [
            PermissionTuple(self.user, 'group_perm', 'group', self.group,
                            self.resource, False, True)]

        check_one_in_other(perms, second)

    def test_resources_with_user_perms(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource.perms_for_user(
            self.user, db_session=db_session)
        second = [PermissionTuple(self.user, 'foo_perm', 'user', None,
                                  self.resource, False, True),
                  PermissionTuple(self.user, 'group_perm', 'group',
                                  self.group, self.resource, False, True),
                  PermissionTuple(self.user, 'test_perm2', 'user', None,
                                  self.resource, False, True)]

        check_one_in_other(perms, second)

    def test_resource_users_for_perm(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource.users_for_perm(
            'foo_perm', db_session=db_session)
        second = [PermissionTuple(self.user, 'foo_perm', 'user', None,
                                  self.resource, False, True)]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource.users_for_perm(
            '__any_permission__', db_session=db_session)
        second = [
            PermissionTuple(self.user, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user4, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_resource_2(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource2.users_for_perm(
            '__any_permission__', db_session=db_session)
        second = [
            PermissionTuple(self.user2, 'foo_perm', 'user', None,
                            self.resource2, False, True),
            PermissionTuple(self.user3, 'test_perm', 'user', None,
                            self.resource2, False, True),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_users(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource.users_for_perm('__any_permission__',
                                             user_ids=[self.user.id],
                                             db_session=db_session)
        second = [
            PermissionTuple(self.user, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True)
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource.users_for_perm('__any_permission__',
                                             user_ids=[self.user.id],
                                             group_ids=[self.group2.id],
                                             db_session=db_session)
        second = [
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True)
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group_other_user_3(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource2.users_for_perm('__any_permission__',
                                              user_ids=[self.user3.id],
                                              db_session=db_session)
        second = [
            PermissionTuple(self.user3, 'test_perm', 'user', None,
                            self.resource2, False, True)
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group_other_user_4(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = self.resource.users_for_perm('__any_permission__',
                                             user_ids=[self.user4.id],
                                             group_ids=[self.group2.id],
                                             db_session=db_session)
        second = [
            PermissionTuple(self.user4, 'group_perm', 'group', self.group2,
                            self.resource, False, True)
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group_ownage(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        resource = TestResourceB(resource_id=99,
                                 resource_name='other',
                                 owner_user_id=self.user2.id)
        group3 = add_group(db_session,'group 3')
        user2_permission = UserResourcePermission(
            perm_name='foo_perm',
            user_id=self.user2.id,
        )
        group3_permission = GroupResourcePermission(
            perm_name='group_perm',
            group_id=group3.id
        )
        resource.group_permissions.append(group3_permission)
        resource.user_permissions.append(user2_permission)
        group3.users.append(self.user3)
        self.user.resources.append(resource)
        self.group2.resources.append(resource)
        db_session.flush()
        perms = resource.users_for_perm('__any_permission__',
                                        db_session=db_session)
        second = [
            PermissionTuple(self.user2, 'foo_perm', 'user', None, resource,
                            False, True),
            PermissionTuple(self.user, ALL_PERMISSIONS, 'user', None, resource,
                            True, True),
            PermissionTuple(self.user4, ALL_PERMISSIONS, 'group', self.group2,
                            resource, True, True),
            PermissionTuple(self.user3, 'group_perm', 'group', group3,
                            resource, False, True)
        ]

        check_one_in_other(perms, second)

    def test_users_for_perms(self, db_session):
        user = User(user_name='aaa', email='aaa', status=0)
        user.set_password('password')
        aaa_perm = UserPermission(perm_name='aaa')
        bbb_perm = UserPermission(perm_name='bbb')
        bbb2_perm = UserPermission(perm_name='bbb')
        user.user_permissions.append(aaa_perm)
        user.user_permissions.append(bbb_perm)
        user2 = User(user_name='bbb', email='bbb', status=0)
        user2.set_password('password')
        user2.user_permissions.append(bbb2_perm)
        user3 = User(user_name='ccc', email='ccc', status=0)
        user3.set_password('password')
        group = add_group(db_session,)
        group.users.append(user3)
        db_session.add(user)
        db_session.add(user2)
        db_session.flush()
        users = User.users_for_perms(['aaa'], db_session=db_session)
        assert len(users.all()) == 1
        assert users[0].user_name == 'aaa'
        users = User.users_for_perms(['bbb'], db_session=db_session).all()
        assert len(users) == 2
        assert ['aaa', 'bbb'] == sorted([u.user_name for u in users])
        users = User.users_for_perms(['aaa', 'bbb', 'manage_apps'],
                                     db_session=db_session)
        assert ['aaa', 'bbb', 'ccc'] == sorted([u.user_name for u in users])

    def test_resources_with_possible_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        resource = TestResourceB(resource_id=3,
                                 resource_name='other',
                                 owner_user_id=self.user.id)
        self.user.resources.append(resource)
        resource_g = TestResourceB(resource_id=4,
                                   resource_name='group owned')
        self.group.resources.append(resource_g)
        db_session.flush()
        perms = self.user.resources_with_possible_perms()
        second = [PermissionTuple(self.user, 'foo_perm', 'user', None,
                                  self.resource, False, True),
                  PermissionTuple(self.user, 'group_perm', 'group',
                                  self.group, self.resource, False, True),
                  PermissionTuple(self.user, 'test_perm2', 'user', None,
                                  self.resource, False, True),
                  PermissionTuple(self.user, ALL_PERMISSIONS, 'user', None,
                                  resource, True, True),
                  PermissionTuple(self.user, ALL_PERMISSIONS, 'group',
                                  self.group, resource_g, True, True),
                  ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_additional_users(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = self.resource.users_for_perm(
            '__any_permission__', db_session=db_session)
        second = [
            PermissionTuple(self.user, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user6, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user7, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user6, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user7, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user4, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_limited_group_perms(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = self.resource.users_for_perm(
            '__any_permission__', limit_group_permissions=True,
            db_session=db_session)
        second = [
            PermissionTuple(None, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
        ]

        check_one_in_other(perms, second)

    def test_resource_groups_for_any_perm_additional_users(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = self.resource.groups_for_perm(
            '__any_permission__', db_session=db_session)
        second = [
            PermissionTuple(self.user, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user6, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user7, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user6, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(user7, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user4, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
        ]

        check_one_in_other(perms, second)

    def test_resource_groups_for_any_perm_just_group_perms_limited(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = self.resource.groups_for_perm(
            '__any_permission__', limit_group_permissions=True,
            db_session=db_session)
        second = [
            PermissionTuple(None, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_excluding_group_perms(
            self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = self.resource.users_for_perm(
            '__any_permission__', limit_group_permissions=True,
            skip_group_perms=True, db_session=db_session)
        second = [
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True)
        ]

        check_one_in_other(perms, second)

    def test_resource_groups_for_any_perm_just_group_perms_limited_empty_group(
        self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)

        group3 = add_group(db_session,'Empty group')
        perm3 = GroupResourcePermission(
            perm_name='group_permx',
            resource_id=self.resource.resource_id
        )
        group3.resource_permissions.append(perm3)
        perms = self.resource.groups_for_perm(
            '__any_permission__', limit_group_permissions=True,
            db_session=db_session)

        second = [
            PermissionTuple(None, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
            PermissionTuple(None, 'group_permx', 'group', group3,
                            self.resource, False, True)
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_limited_group_perms_empty_group(
            self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session,6, 'user 6')
        user7 = add_user(db_session,7, 'user 7')
        perm2 = GroupResourcePermission(
            perm_name='group_perm2',
            resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        group3 = add_group(db_session,'Empty group')
        perm3 = GroupResourcePermission(
            perm_name='group_permx',
            resource_id=self.resource.resource_id
        )
        group3.resource_permissions.append(perm3)

        perms = self.resource.users_for_perm(
            '__any_permission__', limit_group_permissions=True,
            db_session=db_session)

        second = [
            PermissionTuple(None, 'group_perm', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm2', 'group', self.group,
                            self.resource, False, True),
            PermissionTuple(self.user, 'test_perm2', 'user', None,
                            self.resource, False, True),
            PermissionTuple(self.user, 'foo_perm', 'user', None,
                            self.resource, False, True),
            PermissionTuple(None, 'group_perm', 'group', self.group2,
                            self.resource, False, True),
            PermissionTuple(None, 'group_permx', 'group', group3,
                            self.resource, False, True),
        ]

        check_one_in_other(perms, second)


class TestGroup(BaseTestCase):
    def test_add_group(self, db_session):
        group = Group(
            group_name='example group',
            description='example description'
        )
        db_session.add(group)
        db_session.flush()

        group = db_session.query(Group)
        group = group.filter(Group.group_name == 'example group').first()

        assert group.group_name == 'example group'
        assert group.description == 'example description'
        assert group.member_count == 0

    def test_group_repr(self, db_session):
        group = add_group(db_session,)
        assert repr(group) == '<Group: group, 1>'

    def test_by_group_name(self, db_session):
        added_group = add_group(db_session,)
        queried_group = Group.by_group_name('group',
                                            db_session=db_session)

        assert added_group == queried_group

    def test_by_group_name_wrong_groupname(self, db_session):
        add_group(db_session,)
        queried_group = Group.by_group_name('not existing group',
                                            db_session=db_session)

        assert queried_group is None

    def test_users(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        user2 = add_user(db_session,'user2', 'email2')

        group = add_group(db_session,)
        group.users.append(user1)
        group.users.append(user2)

        assert group.users[0] == user1
        assert group.users[1] == user2

    def test_users_dynamic(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        user2 = add_user(db_session,'user2', 'email2')

        group = add_group(db_session,)
        group.users.append(user1)
        group.users.append(user2)
        group_users = group.users_dynamic.all()

        assert group_users[0] == user1
        assert group_users[1] == user2

    def test_all(self, db_session):
        group1 = add_group(db_session,'group1')
        group2 = add_group(db_session,'group2')

        all_groups = Group.all(db_session=db_session).all()

        assert len(all_groups) == 2
        assert all_groups[0] == group1
        assert all_groups[1] == group2

    def test_user_paginator(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        user2 = add_user(db_session,'user2', 'email2')

        group = add_group(db_session,)
        group.users.append(user1)
        group.users.append(user2)
        users_count = len(group.users)
        get_params = {'foo': 'bar', 'baz': 'xxx'}

        paginator = group.get_user_paginator(1, users_count,
                                             GET_params=get_params)

        assert paginator.page == 1
        assert paginator.first_item == 1
        assert paginator.last_item == 2
        assert paginator.items == [user1, user2]
        assert paginator.items == [user1, user2]
        assert paginator.items == [user1, user2]
        assert paginator.items == [user1, user2]

    def test_user_paginator_usernames(self, db_session):
        user1 = add_user(db_session,'user1', 'email1')
        user2 = add_user(db_session,'user2', 'email2')
        user3 = add_user(db_session,'user3', 'email3')

        group = add_group(db_session,)
        group.users.append(user1)
        group.users.append(user2)
        group.users.append(user3)

        # TODO: users count when filtering on names?
        paginator = group.get_user_paginator(1,
                                             user_ids=[1, 3])

        assert paginator.page == 1
        assert paginator.first_item == 1
        assert paginator.last_item == 2
        assert paginator.items == [user1, user3]
        assert paginator.item_count == 2
        assert paginator.page_count == 1


class TestGroupPermission(BaseTestCase):
    def test_repr(self, db_session):
        group_permission = GroupPermission(group_id=1,
                                           perm_name='perm')
        assert repr(group_permission) == '<GroupPermission: perm>'

    def test_by_group_and_perm(self, db_session):
        add_group(db_session,)
        queried = GroupPermission.by_group_and_perm(1, 'manage_apps',
                                                    db_session=db_session)
        assert queried.group_id == 1
        assert queried.perm_name == 'manage_apps'

    def test_by_group_and_perm_wrong_group(self, db_session):
        add_group(db_session,)
        queried = GroupPermission.by_group_and_perm(2,
                                                    'manage_apps',
                                                    db_session=db_session)
        assert queried is None

    def test_by_group_and_perm_wrong_perm(self, db_session):
        add_group(db_session,)
        queried = GroupPermission.by_group_and_perm(1, 'wrong_perm',
                                                    db_session=db_session)
        assert queried is None

    def test_resources_with_possible_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perms = self.group.resources_with_possible_perms()
        second = [PermissionTuple(None, 'group_perm', 'group', self.group,
                                  self.resource, False, True),
                  ]

        check_one_in_other(perms, second)

    def test_resources_with_possible_perms_group2(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        resource3 = add_resource_b(db_session,3, 'other resource')
        self.group2.resources.append(resource3)
        group_permission2 = GroupResourcePermission(
            perm_name='group_perm2',
            group_id=self.group2.id,
        )
        self.resource2.group_permissions.append(group_permission2)

        perms = self.group2.resources_with_possible_perms()
        second = [PermissionTuple(None, 'group_perm', 'group', self.group2,
                                  self.resource, False, True),
                  PermissionTuple(None, 'group_perm2', 'group', self.group2,
                                  self.resource2, False, True),
                  PermissionTuple(None, ALL_PERMISSIONS, 'group', self.group2,
                                  resource3, True, True),
                  ]

        check_one_in_other(perms, second)


class TestUserPermission(BaseTestCase):
    def test_repr(self, db_session):
        user_permission = UserPermission(user_id=1, perm_name='perm')
        assert repr(user_permission) == '<UserPermission: perm>'

    def test_by_user_and_perm(self, db_session):
        add_user(db_session)
        user_permission = UserPermission.by_user_and_perm(1, 'root',
                                                          db_session=db_session)

        assert user_permission.user_id == 1
        assert user_permission.perm_name == 'root'

    def test_by_user_and_perm_wrong_username(self, db_session):
        add_user(db_session)
        user_permission = UserPermission.by_user_and_perm(999, 'root',
                                                          db_session=db_session)

        assert user_permission is None

    def test_by_user_and_perm_wrong_permname(self, db_session):
        add_user(db_session)
        user_permission = UserPermission.by_user_and_perm(1, 'wrong',
                                                          db_session=db_session)

        assert user_permission is None


class TestUserGroup(BaseTestCase):
    def test_repr(self, db_session):
        user_group = UserGroup(user_id=1, group_id=1)

        assert repr(user_group) == '<UserGroup: g:1, u:1>'


class TestGroupResourcePermission(BaseTestCase):
    def test_repr(self, db_session):
        group_resource_perm = GroupResourcePermission(group_id=1,
                                                      resource_id=1,
                                                      perm_name='perm')
        assert repr(
            group_resource_perm) == '<GroupResourcePermission: g:1, perm, r:1>'


class TestAddResource(BaseTestCase):
    def test_pkey(self, db_session):
        resource = add_resource(db_session,99, 'some random name')
        assert resource.resource_id == 99

    def test_nopkey(self, db_session):
        resource = add_resource(db_session,None, 'some random name')
        assert resource.resource_id == 1


class TestExternalIdentity(BaseTestCase):
    def test_by_external_id_and_provider(self, db_session):
        user = add_user(db_session)
        identity = ExternalIdentity(external_user_name='foo',
                                    external_id='foo',
                                    provider_name='facebook')
        user.external_identities.append(identity)
        # db_session.flush()
        found = ExternalIdentityService.by_external_id_and_provider(
            provider_name='facebook',
            external_id='foo',
            db_session=db_session)
        assert identity == found

    def test_user_by_external_id_and_provider(self, db_session):
        user = add_user(db_session)
        identity = ExternalIdentity(external_user_name='foo',
                                    external_id='foo',
                                    provider_name='facebook')
        user.external_identities.append(identity)
        # db_session.flush()
        found = ExternalIdentityService.user_by_external_id_and_provider(
            provider_name='facebook',
            external_id='foo',
            db_session=db_session)
        assert user == found


class TestUtils(BaseTestCase):
    def test_permission_to_04_acls(self, db_session):
        pass


if __name__ == '__main__':
    pass
