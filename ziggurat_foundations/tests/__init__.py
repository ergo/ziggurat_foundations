# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

from ziggurat_foundations.tests.conftest import (
    User,
    Group,
    GroupPermission,
    UserPermission,
    UserResourcePermission,
    GroupResourcePermission,
    Resource,
    ResourceTestObj,
    ResourceTestobjB,
)
from ziggurat_foundations.models.services.user import UserService


def check_one_in_other(first, second):
    while first:
        item = first.pop()
        ix = second.index(item)
        second.pop(ix)
    assert len(first) == len(second)


def add_user(
    db_session,
    user_name="username",
    email="email",
    perms=["root", "alter_users"],
    password="password",
):
    user = User(user_name=user_name, email=email, status=0)
    UserService.set_password(user, password)
    for perm in perms:
        u_perm = UserPermission(perm_name=perm)
        user.user_permissions.append(u_perm)
    db_session.add(user)
    db_session.flush()
    return user


def add_resource(
    db_session,
    resource_id,
    resource_name="test_resource",
    parent_id=None,
    ordering=None,
):
    Resource.__possible_permissions__ = [
        "test_perm",
        "test_perm1",
        "test_perm2",
        "foo_perm",
        "group_perm",
        "group_perm2",
    ]
    resource = ResourceTestObj(
        resource_id=resource_id,
        resource_name=resource_name,
        parent_id=parent_id,
        ordering=ordering,
    )
    db_session.add(resource)
    db_session.flush()
    return resource


def add_resource_b(db_session, resource_id, resource_name="test_resource"):
    Resource.__possible_permissions__ = [
        "test_perm",
        "test_perm1",
        "test_perm2",
        "foo_perm",
        "group_perm",
        "group_perm2",
    ]
    resource = ResourceTestobjB(resource_id=resource_id, resource_name=resource_name)
    db_session.add(resource)
    db_session.flush()
    return resource


def add_group(db_session, group_name="group", description="desc"):
    group = Group(group_name=group_name, description=description)
    test_perm = GroupPermission(perm_name="manage_apps")
    group.permissions.append(test_perm)
    db_session.add(group)
    db_session.flush()
    return group


def create_default_tree(db_session):
    root = add_resource(db_session, -1, "root a", ordering=1)
    res_a = add_resource(db_session, 1, "a", parent_id=root.resource_id, ordering=1)
    add_resource(db_session, 5, "aa", parent_id=res_a.resource_id, ordering=1)
    add_resource(db_session, 6, "ab", parent_id=res_a.resource_id, ordering=2)
    res_ac = add_resource(db_session, 7, "ac", parent_id=res_a.resource_id, ordering=3)
    res_aca = add_resource(
        db_session, 9, "aca", parent_id=res_ac.resource_id, ordering=1
    )
    add_resource(db_session, 12, "acaa", parent_id=res_aca.resource_id, ordering=1)
    add_resource(db_session, 8, "ad", parent_id=res_a.resource_id, ordering=4)
    res_b = add_resource(db_session, 2, "b", parent_id=root.resource_id, ordering=2)
    add_resource(db_session, 4, "ba", parent_id=res_b.resource_id, ordering=1)
    add_resource(db_session, 3, "c", parent_id=root.resource_id, ordering=3)
    add_resource(db_session, 10, "d", parent_id=root.resource_id, ordering=4)
    add_resource(db_session, 11, "e", parent_id=root.resource_id, ordering=5)
    root_b = add_resource(db_session, -2, "root b", ordering=2)
    root_c = add_resource(db_session, -3, "root c", ordering=3)
    return [root, root_b, root_c]


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
        created_user = add_user(db_session, user_name="first_user")
        created_user2 = add_user(
            db_session, user_name="foouser", email="new_email", perms=["custom"]
        )
        created_user3 = add_user(db_session, user_name="baruser", email="new_email2")
        created_user4 = add_user(db_session, user_name="bazuser", email="new_email3")
        resource = add_resource(db_session, 1, "test_resource")
        resource2 = add_resource_b(db_session, 2, "other_resource")
        group = add_group(db_session)
        group2 = add_group(db_session, group_name="group2")
        group.users.append(created_user)
        group2.users.append(created_user4)
        group_permission = GroupResourcePermission(
            perm_name="group_perm", group_id=group.id
        )
        group_permission2 = GroupResourcePermission(
            perm_name="group_perm", group_id=group2.id
        )
        user_permission = UserResourcePermission(
            perm_name="test_perm2", user_id=created_user.id
        )
        user_permission2 = UserResourcePermission(
            perm_name="foo_perm", user_id=created_user.id
        )
        user2_permission = UserResourcePermission(
            perm_name="foo_perm", user_id=created_user2.id
        )
        user3_permission = UserResourcePermission(
            perm_name="test_perm", user_id=created_user3.id
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
        self.user_name = "new_name"
        self.user_password = "foo"
        self.email = "change@email.com"
