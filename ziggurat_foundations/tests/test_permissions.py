# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

import pytest

from ziggurat_foundations.models.services.group_permission import GroupPermissionService
from ziggurat_foundations.models.services.group_resource_permission import (
    GroupResourcePermissionService,
)
from ziggurat_foundations.models.services.user_permission import UserPermissionService
from ziggurat_foundations.models.services.user_resource_permission import (
    UserResourcePermissionService,
)

from ziggurat_foundations.models.services.resource import ResourceService

from ziggurat_foundations.permissions import PermissionTuple, ALL_PERMISSIONS
from ziggurat_foundations.tests import (
    add_user,
    check_one_in_other,
    add_resource,
    add_resource_b,
    add_group,
    BaseTestCase,
)
from ziggurat_foundations.tests.conftest import (
    User,
    UserPermission,
    GroupPermission,
    UserResourcePermission,
    GroupResourcePermission,
    ResourceTestobjB,
)
from ziggurat_foundations.models.services.group import GroupService
from ziggurat_foundations.models.services.user import UserService


class TestUserPermissions(BaseTestCase):
    def test_user_permissions(self, db_session):
        created_user = add_user(db_session)
        permissions = UserService.permissions(created_user, db_session=db_session)
        expected = [
            PermissionTuple(
                created_user, "alter_users", "user", None, None, False, True
            ),
            PermissionTuple(created_user, "root", "user", None, None, False, True),
        ]
        check_one_in_other(permissions, expected)

    def test_owned_permissions(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        created_user.resources.append(resource)
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user, ["test_perm"], db_session=db_session
        ).all()
        assert resources[0] == resource
        permission = ResourceService.direct_perms_for_user(resource, created_user)[0]
        assert permission.owner is True
        assert permission.allowed is True
        assert permission.user.id == created_user.id

    def test_resources_with_perm(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user, ["test_perm"], db_session=db_session
        ).all()
        assert resources[0] == resource

    def test_mixed_perms(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        resource2 = add_resource(db_session, 2, "test_resource")
        created_user.resources.append(resource2)
        add_resource(db_session, 3, "test_resource")
        add_resource_b(db_session, 4, "test_resource")
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user, ["test_perm"], db_session=db_session
        ).all()
        found_ids = [r.resource_id for r in resources]
        assert sorted(found_ids) == [1, 2]

    def test_resources_with_perm_type_found(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user,
            ["test_perm"],
            resource_types=["test_resource"],
            db_session=db_session,
        ).all()
        assert resources[0] == resource

    def test_resources_with_perm_type_not_found(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user,
            ["test_perm"],
            resource_types=["test_resource_b"],
            db_session=db_session,
        ).all()
        assert resources == []

    def test_resources_with_perm_type_other_found(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        resource2 = add_resource_b(db_session, 2, "test_resource")
        resource3 = add_resource(db_session, 3, "test_resource")
        resource4 = add_resource_b(db_session, 4, "test_resource")
        db_session.flush()
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        permission2 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource2.resource_id,
        )
        resource2.user_permissions.append(permission2)
        permission3 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource3.resource_id,
        )
        resource3.user_permissions.append(permission3)
        permission4 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource4.resource_id,
        )
        resource4.user_permissions.append(permission4)
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user,
            ["test_perm"],
            resource_types=["test_resource_b"],
            db_session=db_session,
        ).all()
        assert len(resources) == 2

    def test_resources_with_wrong_perm(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm_bad",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        with pytest.raises(AssertionError):
            resource.user_permissions.append(permission)

    def test_multiple_resources_with_perm(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        resource2 = add_resource(db_session, 2, "test_resource2")
        permission2 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource2.resource_id,
        )
        resource2.user_permissions.append(permission2)
        resources = UserService.resources_with_perms(
            created_user, ["test_perm"], db_session=db_session
        ).all()
        assert resources == [resource, resource2]

    def test_resources_ids_with_perm(self, db_session):
        created_user = add_user(db_session)
        resource1 = add_resource(db_session, 1, "test_resource1")
        resource2 = add_resource(db_session, 2, "test_resource2")
        resource3 = add_resource(db_session, 3, "test_resource3")

        permission1 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource1.resource_id,
        )
        permission2 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource2.resource_id,
        )
        permission3 = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource3.resource_id,
        )

        resource1.user_permissions.append(permission1)
        resource2.user_permissions.append(permission2)
        resource3.user_permissions.append(permission3)

        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user, ["test_perm"], resource_ids=[1, 3], db_session=db_session
        ).all()
        assert resources == [resource1, resource3]

    def test_resources_with_wrong_group_permission(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        group = add_group(db_session)
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
            perm_name="test_perm_bad",
            group_id=group.id,
            resource_id=resource.resource_id,
        )
        with pytest.raises(AssertionError):
            resource.group_permissions.append(group_permission)

    def test_resources_with_group_permission(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        resource2 = add_resource(db_session, 2, "test_resource2")
        add_resource(db_session, 3, "test_resource3")
        group = add_group(db_session)
        group.users.append(created_user)
        group_permission = GroupResourcePermission(
            perm_name="test_perm", group_id=1, resource_id=resource.resource_id
        )
        group_permission2 = GroupResourcePermission(
            perm_name="foo_perm", group_id=1, resource_id=resource2.resource_id
        )
        resource.group_permissions.append(group_permission)
        resource2.group_permissions.append(group_permission2)
        db_session.flush()
        resources = UserService.resources_with_perms(
            created_user, ["foo_perm"], db_session=db_session
        ).all()
        assert resources[0] == resource2

    def test_resources_with_direct_user_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        # test_perm1 from group perms should be ignored
        perms = ResourceService.direct_perms_for_user(
            self.resource, self.user, db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resources_with_direct_group_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        # test_perm1 from group perms should be ignored
        perms = ResourceService.group_perms_for_user(
            self.resource, self.user, db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            )
        ]

        check_one_in_other(perms, second)

    def test_resources_with_user_perms(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.perms_for_user(
            self.resource, self.user, db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_perm(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource, "foo_perm", db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            )
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource, "__any_permission__", db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user4,
                "group_perm",
                "group",
                self.group2,
                self.resource,
                False,
                True,
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_resource_2(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource2, "__any_permission__", db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user2, "foo_perm", "user", None, self.resource2, False, True
            ),
            PermissionTuple(
                self.user3, "test_perm", "user", None, self.resource2, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_users(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource,
            "__any_permission__",
            user_ids=[self.user.id],
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource,
            "__any_permission__",
            user_ids=[self.user.id],
            group_ids=[self.group2.id],
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group_other_user_3(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource2,
            "__any_permission__",
            user_ids=[self.user3.id],
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                self.user3, "test_perm", "user", None, self.resource2, False, True
            )
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group_other_user_4(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        perms = ResourceService.users_for_perm(
            self.resource,
            "__any_permission__",
            user_ids=[self.user4.id],
            group_ids=[self.group2.id],
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                self.user4,
                "group_perm",
                "group",
                self.group2,
                self.resource,
                False,
                True,
            )
        ]

        check_one_in_other(perms, second)

    def test_resource_users_limited_group_ownage(self, db_session):
        self.maxDiff = 9999
        self.set_up_user_group_and_perms(db_session)
        resource = ResourceTestobjB(
            resource_id=99, resource_name="other", owner_user_id=self.user2.id
        )
        group3 = add_group(db_session, "group 3")
        user2_permission = UserResourcePermission(
            perm_name="foo_perm", user_id=self.user2.id
        )
        group3_permission = GroupResourcePermission(
            perm_name="group_perm", group_id=group3.id
        )
        resource.group_permissions.append(group3_permission)
        resource.user_permissions.append(user2_permission)
        group3.users.append(self.user3)
        self.user.resources.append(resource)
        self.group2.resources.append(resource)
        db_session.flush()
        perms = ResourceService.users_for_perm(
            resource, "__any_permission__", db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user2, "foo_perm", "user", None, resource, False, True
            ),
            PermissionTuple(
                self.user, ALL_PERMISSIONS, "user", None, resource, True, True
            ),
            PermissionTuple(
                self.user4, ALL_PERMISSIONS, "group", self.group2, resource, True, True
            ),
            PermissionTuple(
                self.user3, "group_perm", "group", group3, resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_users_for_perms(self, db_session):
        user = User(user_name="aaa", email="aaa", status=0)
        UserService.set_password(user, "password")
        aaa_perm = UserPermission(perm_name="aaa")
        bbb_perm = UserPermission(perm_name="bbb")
        bbb2_perm = UserPermission(perm_name="bbb")
        user.user_permissions.append(aaa_perm)
        user.user_permissions.append(bbb_perm)
        user2 = User(user_name="bbb", email="bbb", status=0)
        UserService.set_password(user2, "password")
        user2.user_permissions.append(bbb2_perm)
        user3 = User(user_name="ccc", email="ccc", status=0)
        UserService.set_password(user3, "password")
        group = add_group(db_session)
        group.users.append(user3)
        db_session.add(user)
        db_session.add(user2)
        db_session.flush()
        users = UserService.users_for_perms(["aaa"], db_session=db_session)
        assert len(users.all()) == 1
        assert users[0].user_name == "aaa"
        users = UserService.users_for_perms(["bbb"], db_session=db_session).all()
        assert len(users) == 2
        assert ["aaa", "bbb"] == sorted([u.user_name for u in users])
        users = UserService.users_for_perms(
            ["aaa", "bbb", "manage_apps"], db_session=db_session
        )
        assert ["aaa", "bbb", "ccc"] == sorted([u.user_name for u in users])

    def test_resources_with_possible_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        resource = ResourceTestobjB(
            resource_id=3, resource_name="other", owner_user_id=self.user.id
        )
        self.user.resources.append(resource)
        resource_g = ResourceTestobjB(resource_id=4, resource_name="group owned")
        self.group.resources.append(resource_g)
        db_session.flush()
        perms = UserService.resources_with_possible_perms(
            self.user, db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, ALL_PERMISSIONS, "user", None, resource, True, True
            ),
            PermissionTuple(
                self.user, ALL_PERMISSIONS, "group", self.group, resource_g, True, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_additional_users(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = ResourceService.users_for_perm(
            self.resource, "__any_permission__", db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                user6, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                user7, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user,
                "group_perm2",
                "group",
                self.group,
                self.resource,
                False,
                True,
            ),
            PermissionTuple(
                user6, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                user7, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user4,
                "group_perm",
                "group",
                self.group2,
                self.resource,
                False,
                True,
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_limited_group_perms(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = ResourceService.users_for_perm(
            self.resource,
            "__any_permission__",
            limit_group_permissions=True,
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                None, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm", "group", self.group2, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_groups_for_any_perm_additional_users(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = ResourceService.groups_for_perm(
            self.resource, "__any_permission__", db_session=db_session
        )
        second = [
            PermissionTuple(
                self.user, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                user6, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                user7, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user,
                "group_perm2",
                "group",
                self.group,
                self.resource,
                False,
                True,
            ),
            PermissionTuple(
                user6, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                user7, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user4,
                "group_perm",
                "group",
                self.group2,
                self.resource,
                False,
                True,
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_groups_for_any_perm_just_group_perms_limited(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = ResourceService.groups_for_perm(
            self.resource,
            "__any_permission__",
            limit_group_permissions=True,
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                None, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm", "group", self.group2, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_excluding_group_perms(self, db_session):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        perms = ResourceService.users_for_perm(
            self.resource,
            "__any_permission__",
            limit_group_permissions=True,
            skip_group_perms=True,
            db_session=db_session,
        )
        second = [
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_groups_for_any_perm_just_group_perms_limited_empty_group(
        self, db_session
    ):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)

        group3 = add_group(db_session, "Empty group")
        perm3 = GroupResourcePermission(
            perm_name="group_permx", resource_id=self.resource.resource_id
        )
        group3.resource_permissions.append(perm3)
        perms = ResourceService.groups_for_perm(
            self.resource,
            "__any_permission__",
            limit_group_permissions=True,
            db_session=db_session,
        )

        second = [
            PermissionTuple(
                None, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm", "group", self.group2, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_permx", "group", group3, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_resource_users_for_any_perm_limited_group_perms_empty_group(
        self, db_session
    ):
        self.maxDiff = 99999
        self.set_up_user_group_and_perms(db_session)
        user6 = add_user(db_session, 6, "user 6")
        user7 = add_user(db_session, 7, "user 7")
        perm2 = GroupResourcePermission(
            perm_name="group_perm2", resource_id=self.resource.resource_id
        )
        self.group.resource_permissions.append(perm2)
        self.group.users.append(user6)
        self.group.users.append(user7)
        group3 = add_group(db_session, "Empty group")
        perm3 = GroupResourcePermission(
            perm_name="group_permx", resource_id=self.resource.resource_id
        )
        group3.resource_permissions.append(perm3)

        perms = ResourceService.users_for_perm(
            self.resource,
            "__any_permission__",
            limit_group_permissions=True,
            db_session=db_session,
        )

        second = [
            PermissionTuple(
                None, "group_perm", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm2", "group", self.group, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "test_perm2", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                self.user, "foo_perm", "user", None, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm", "group", self.group2, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_permx", "group", group3, self.resource, False, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_get_resource_permission(self, db_session):
        created_user = add_user(db_session)
        resource = add_resource(db_session, 1, "test_resource")
        permission = UserResourcePermission(
            perm_name="test_perm",
            user_id=created_user.id,
            resource_id=resource.resource_id,
        )
        resource.user_permissions.append(permission)
        db_session.flush()
        perm = UserResourcePermissionService.get(
            user_id=created_user.id,
            resource_id=resource.resource_id,
            perm_name="test_perm",
            db_session=db_session,
        )
        assert perm.perm_name == "test_perm"
        assert perm.resource_id == resource.resource_id
        assert perm.user_id == created_user.id


class TestGroupPermission(BaseTestCase):
    def test_repr(self, db_session):
        group_permission = GroupPermission(group_id=1, perm_name="perm")
        assert repr(group_permission) == "<GroupPermission: perm>"

    def test_get(self, db_session):
        org_group = add_group(db_session, "group1")
        group = GroupPermissionService.get(
            group_id=org_group.id, perm_name="manage_apps", db_session=db_session
        )
        assert group.group_id == 1
        assert group.perm_name == "manage_apps"

    def test_by_group_and_perm(self, db_session):
        add_group(db_session)
        queried = GroupPermissionService.by_group_and_perm(
            1, "manage_apps", db_session=db_session
        )
        assert queried.group_id == 1
        assert queried.perm_name == "manage_apps"

    def test_by_group_and_perm_wrong_group(self, db_session):
        add_group(db_session)
        queried = GroupPermissionService.by_group_and_perm(
            2, "manage_apps", db_session=db_session
        )
        assert queried is None

    def test_by_group_and_perm_wrong_perm(self, db_session):
        add_group(db_session)
        queried = GroupPermissionService.by_group_and_perm(
            1, "wrong_perm", db_session=db_session
        )
        assert queried is None

    def test_resources_with_possible_perms(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perms = GroupService.resources_with_possible_perms(self.group)
        second = [
            PermissionTuple(
                None, "group_perm", "group", self.group, self.resource, False, True
            )
        ]

        check_one_in_other(perms, second)

    def test_resources_with_possible_perms_group2(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        resource3 = add_resource_b(db_session, 3, "other resource")
        self.group2.resources.append(resource3)
        group_permission2 = GroupResourcePermission(
            perm_name="group_perm2", group_id=self.group2.id
        )
        self.resource2.group_permissions.append(group_permission2)

        perms = GroupService.resources_with_possible_perms(self.group2)
        second = [
            PermissionTuple(
                None, "group_perm", "group", self.group2, self.resource, False, True
            ),
            PermissionTuple(
                None, "group_perm2", "group", self.group2, self.resource2, False, True
            ),
            PermissionTuple(
                None, ALL_PERMISSIONS, "group", self.group2, resource3, True, True
            ),
        ]

        check_one_in_other(perms, second)

    def test_group_resource_permission(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        add_resource_b(db_session, 3, "other resource")
        db_session.flush()
        group_permission2 = GroupResourcePermission(
            perm_name="group_perm2", group_id=self.group2.id
        )
        row = GroupResourcePermissionService.get(
            group_id=self.group2.id,
            resource_id=self.resource2.resource_id,
            perm_name="group_perm2",
            db_session=db_session,
        )
        assert row is None
        self.resource2.group_permissions.append(group_permission2)
        row = GroupResourcePermissionService.get(
            group_id=self.group2.id,
            resource_id=self.resource2.resource_id,
            perm_name="group_perm2",
            db_session=db_session,
        )
        assert row is not None

    def test_group_resource_permission_wrong(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perm_name = "group_permX"
        perm = ResourceService.perm_by_group_and_perm_name(
            resource_id=self.resource.resource_id,
            group_id=self.group.id,
            perm_name=perm_name,
            db_session=db_session,
        )
        assert perm is None

    def test_group_resource_permission2(self, db_session):
        self.set_up_user_group_and_perms(db_session)
        perm_name = "group_perm"
        perm = ResourceService.perm_by_group_and_perm_name(
            resource_id=self.resource.resource_id,
            group_id=self.group.id,
            perm_name=perm_name,
            db_session=db_session,
        )
        assert perm.group_id == self.group.id
        assert perm.resource_id == self.resource.resource_id
        assert perm.perm_name == perm_name


class TestUserPermission(BaseTestCase):
    def test_repr(self, db_session):
        user_permission = UserPermission(user_id=1, perm_name="perm")
        assert repr(user_permission) == "<UserPermission: perm>"

    def test_get(self, db_session):
        user = add_user(db_session)
        perm = UserPermissionService.get(
            user_id=user.id, perm_name="root", db_session=db_session
        )
        assert perm.user_id == user.id
        assert perm.perm_name == "root"

    def test_by_user_and_perm(self, db_session):
        add_user(db_session)
        user_permission = UserPermissionService.by_user_and_perm(
            1, "root", db_session=db_session
        )

        assert user_permission.user_id == 1
        assert user_permission.perm_name == "root"

    def test_by_user_and_perm_wrong_username(self, db_session):
        add_user(db_session)
        user_permission = UserPermissionService.by_user_and_perm(
            999, "root", db_session=db_session
        )

        assert user_permission is None

    def test_by_user_and_perm_wrong_permname(self, db_session):
        add_user(db_session)
        user_permission = UserPermissionService.by_user_and_perm(
            1, "wrong", db_session=db_session
        )

        assert user_permission is None
