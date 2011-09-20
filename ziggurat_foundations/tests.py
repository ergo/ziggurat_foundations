# -*- coding: utf-8 -*-
import unittest

from sqlalchemy.ext.declarative import declarative_base

import ziggurat_foundations
from ziggurat_foundations.models import UserMixin
from ziggurat_foundations.models import GroupMixin
from ziggurat_foundations.models import GroupPermissionMixin
from ziggurat_foundations.models import UserPermissionMixin
from ziggurat_foundations.models import UserGroupMixin
from ziggurat_foundations.models import UserResourcePermissionMixin
from ziggurat_foundations.models import GroupResourcePermissionMixin
from ziggurat_foundations.models import ResourceMixin
from ziggurat_foundations.models import get_db_session
from ziggurat_foundations import ziggurat_model_init

from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy import create_engine

Base = declarative_base()

class Group(GroupMixin, Base):
    pass

class GroupPermission(GroupPermissionMixin, Base):
    pass

class UserGroup(UserGroupMixin, Base):
    pass

class GroupResourcePermission(GroupResourcePermissionMixin, Base):
    pass

class Resource(ResourceMixin, Base):
    pass

class TestResource(Resource):
    __mapper_args__ = {'polymorphic_identity': u'test_resource'}

class UserPermission(UserPermissionMixin, Base):
    pass

class UserResourcePermission(UserResourcePermissionMixin, Base):
    pass
        
class User(UserMixin, Base):
    pass

ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource)

def _initTestingDB():
    engine = create_engine('sqlite://')
    # pyramid way
    maker = sessionmaker(bind=engine)
    Base.metadata.bind = engine
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return maker()

    # pylons/akhet monkeypatching way
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
    
    def _addResource(self, resource_id, resource_name=u'test_resource',):
        Resource.__possible_permissions__ = [u'test_perm', u'test_perm1',
                                             u'test_perm2',u'foo_perm',
                                             u'group_perm']
        resource = TestResource(resource_id=resource_id,
                            resource_name=resource_name)
        self.session.add(resource)
        self.session.flush()
        return resource

    def _addGroup(self, group_name=u'group', description=u'desc',):
        group = Group(
            group_name=group_name,
            description=description
        )
        self.session.add(group)
        self.session.flush()
        return group

class ModelTestCase(BaseTestCase):
    
    def test_get_keys(self):
        keys = User._get_keys()
        self.assertEqual(len(keys), 7)
        
    def test_get_dict(self):
        created_user = self._addUser()
        dict_ = created_user.get_dict()
        self.assertEqual(len(dict_), 7)
        
    def test_appstruct(self):
        created_user = self._addUser()
        appstruct = created_user.get_appstruct()
        self.assertEqual(len(appstruct), 7)

    def test_populate_obj_appstruct(self):
        created_user = self._addUser()
        app_struct = {'user_name':u'new_name'}
        created_user.populate_obj(app_struct)
        self.assertEqual(created_user.user_name, u'new_name')

#    def test_session(self):
#        session = get_db_session(self._addUser())
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

    def test_by_user_name_existing(self):
        created_user = self._addUser()
        queried_user = User.by_user_name(u'username', db_session=self.session)

        self.assertEqual(created_user, queried_user)

    def test_by_user_name_not_existing(self):
        self._addUser()
        queried_user = User.by_user_name(u'not_existing_user',
                                         db_session=self.session)

        self.assertEqual(queried_user, None)

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

    def test_by_user_names(self):
        user1 = self._addUser(u'user1', u'email1')
        self._addUser(u'user2', u'email2')
        user3 = self._addUser(u'user3', u'email3')

        queried_users = User.by_user_names([u'user1', u'user3'],
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

    def test_by_email(self):
        created_user = self._addUser()
        queried_user = User.by_email(u'email',db_session=self.session)

        self.assertEqual(created_user, queried_user)

    def test_by_email_wrong_email(self):
        self._addUser()
        queried_user = User.by_email(u'wrong_email',db_session=self.session)

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
        
    def test_regenerate_security_code(self):
        created_user = self._addUser()
        old_code = created_user.security_code
        created_user.regenerate_security_code()
        new_code = created_user.security_code
        
        self.assertNotEqual(old_code, new_code)
        self.assertEqual(len(new_code), 32)
        
    def test_user_permissions(self):
        created_user = self._addUser()
        permissions = created_user.permissions
        self.assertEqual(permissions, [(u'username', u'alter_users'),
                                       (u'username', u'root')])
        
    def test_resources_with_perm(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_name=created_user.user_name,
                                            resource_id=resource.resource_id)
        resource.user_permissions.append(permission)
        self.session.flush()
        resources = created_user.resources_with_perms([u'test_perm'],
                                        db_session=self.session).all()
        self.assertEqual(resources[0], resource)
        
    def test_resources_with_wrong_perm(self):
        with self.assertRaises(AssertionError):
            created_user = self._addUser()
            resource = self._addResource(1, u'test_resource')
            permission = UserResourcePermission(perm_name=u'test_perm_BAD',
                                        user_name=created_user.user_name,
                                        resource_id = resource.resource_id
                                                    )
            resource.user_permissions.append(permission)

    def test_multiple_resources_with_perm(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        permission = UserResourcePermission(perm_name=u'test_perm',
                                            user_name=created_user.user_name,
                                            resource_id = resource.resource_id
                                                )
        resource.user_permissions.append(permission)
        resource2 = self._addResource(2, u'test_resource2')
        permission2 = UserResourcePermission(perm_name=u'test_perm',
                                            user_name=created_user.user_name,
                                            resource_id = resource2.resource_id
                                                )
        resource2.user_permissions.append(permission2)
        resources = created_user.resources_with_perms([u'test_perm'],
                                        db_session=self.session).all()
        self.assertEqual(resources, [resource,resource2])
    
    def test_resources_ids_with_perm(self):
        created_user = self._addUser()
        resource1 = self._addResource(1, u'test_resource1')
        resource2 = self._addResource(2, u'test_resource2')
        resource3 = self._addResource(3, u'test_resource3')

        permission1 = UserResourcePermission(perm_name=u'test_perm',
                                            user_name=created_user.user_name,
                                            resource_id=resource1.resource_id)
        permission2 = UserResourcePermission(perm_name=u'test_perm',
                                            user_name=created_user.user_name,
                                            resource_id=resource2.resource_id)
        permission3 = UserResourcePermission(perm_name=u'test_perm',
                                            user_name=created_user.user_name,
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
        with self.assertRaises(AssertionError):
            created_user = self._addUser()
            resource = self._addResource(1, u'test_resource')
            group = self._addGroup()
            group.users.append(created_user)
            group_permission = GroupResourcePermission(
                                        perm_name=u'test_perm_BAD',
                                        group_name=u'group',
                                        resource_id = resource.resource_id
                                                       )
            resource.group_permissions.append(group_permission)
        
    def test_resources_with_group_permission(self):
        created_user = self._addUser()
        resource = self._addResource(1, u'test_resource')
        resource2 = self._addResource(2, u'test_resource2')
        self._addResource(3, u'test_resource3')
        group = self._addGroup()
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
                                    perm_name=u'test_perm',
                                    group_name=u'group',
                                    resource_id = resource.resource_id
                                                   )
        group_permission2 = GroupResourcePermission(
                                    perm_name=u'foo_perm',
                                    group_name=u'group',
                                    resource_id = resource2.resource_id
                                                   )
        resource.group_permissions.append(group_permission)
        resource2.group_permissions.append(group_permission2)
        self.session.flush()
        resources = created_user.resources_with_perms([u'foo_perm'],
                                        db_session=self.session).all()
        self.assertEqual(resources[0],resource2)
        
    
    def __set_up_user_group_and_perms(self):
        created_user = self._addUser()
        created_user2 = self._addUser(user_name=u'foouser',email=u'new_email')
        created_user3 = self._addUser(user_name=u'foouser2',email=u'new_email2')
        created_user4 = self._addUser(user_name=u'foouser3',email=u'new_email3')
        resource = self._addResource(1, u'test_resource')
        group = self._addGroup()
        group2 = self._addGroup(group_name=u'group2')
        group.users.append(created_user)
        group2.users.append(created_user4)
        group_permission = GroupResourcePermission(
                                    perm_name=u'group_perm',
                                    group_name=u'group',
                                    resource_id = resource.resource_id
                                                   )
        group_permission2 = GroupResourcePermission(
                                    perm_name=u'group_perm',
                                    group_name=u'group2',
                                    resource_id = resource.resource_id
                                                   )
        user_permission = UserResourcePermission(
                                    perm_name=u'test_perm2',
                                    user_name=u'username',
                                    resource_id = resource.resource_id
                                                   )
        user_permission2 = UserResourcePermission(
                                    perm_name=u'foo_perm',
                                    user_name=u'username',
                                    resource_id = resource.resource_id
                                                   )
        user_permission3 = UserResourcePermission(
                                    perm_name=u'foo_perm',
                                    user_name=u'foouser',
                                    resource_id = resource.resource_id
                                                   )
        user_permission4 = UserResourcePermission(
                                    perm_name=u'test_perm',
                                    user_name=u'foouser2',
                                    resource_id = resource.resource_id
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
        self.assertEqual(self.resource.direct_perms_for_user(self.user,
                                                    db_session=self.session),
                [(u'username', u'foo_perm'), (u'username', u'test_perm2')]
                         )

    def test_resources_with_direct_group_perms(self):
        self.__set_up_user_group_and_perms()
        # test_perm1 from group perms should be ignored
        self.assertEqual(self.resource.group_perms_for_user(self.user,
                                                db_session=self.session),
                [(u'group:group', u'group_perm')]
                )
        
    def test_resources_with_user_perms(self):
        self.__set_up_user_group_and_perms()
        self.assertEqual(
                sorted(self.resource.perms_for_user(self.user,
                                                    db_session=self.session)),
                sorted([(u'username', u'foo_perm'),
                        (u'group:group', u'group_perm'), 
                        (u'username', u'test_perm2')])
                        )
    
    def test_users_for_perm(self):
        self.__set_up_user_group_and_perms()
        self.assertEqual(
                sorted(self.resource.users_for_perm(u'foo_perm',
                                                    db_session=self.session)),
                sorted([(self.user, u'foo_perm',),(self.user2, u'foo_perm',)])
                        )

    def test_users_for_any_perm(self):
        self.__set_up_user_group_and_perms()
        self.assertEqual(
                sorted(self.resource.users_for_perm('__any_permission__',
                                                    db_session=self.session)),
                sorted([
                        (self.user, u'group_perm',),
                        (self.user, u'test_perm2',),
                        (self.user, u'foo_perm',),
                        (self.user2, u'foo_perm',),
                        (self.user3, u'test_perm',),
                        (self.user4, u'group_perm',),
                        ])
                )
        

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

if __name__ == '__main__':
    unittest.main()  # pragma: nocover
