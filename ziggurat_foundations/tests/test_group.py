# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

from ziggurat_foundations.models.services.group import GroupService
from ziggurat_foundations.models.services import BaseService
from ziggurat_foundations.tests import add_user, add_group, BaseTestCase
from ziggurat_foundations.tests.conftest import Group


class TestGroup(BaseTestCase):
    def test_add_group(self, db_session):
        group = Group(group_name="example group", description="example description")
        db_session.add(group)
        db_session.flush()

        group = db_session.query(Group)
        group = group.filter(Group.group_name == "example group").first()

        assert group.group_name == "example group"
        assert group.description == "example description"
        assert group.member_count == 0

    def test_group_repr(self, db_session):
        group = add_group(db_session)
        assert repr(group) == "<Group: group, 1>"

    def test_by_group_name(self, db_session):
        added_group = add_group(db_session)
        queried_group = GroupService.by_group_name("group", db_session=db_session)

        assert added_group == queried_group

    def test_by_group_name_wrong_groupname(self, db_session):
        add_group(db_session)
        queried_group = GroupService.by_group_name(
            "not existing group", db_session=db_session
        )

        assert queried_group is None

    def test_users(self, db_session):
        user1 = add_user(db_session, "user1", "email1")
        user2 = add_user(db_session, "user2", "email2")

        group = add_group(db_session)
        group.users.append(user1)
        group.users.append(user2)

        assert group.users[0] == user1
        assert group.users[1] == user2

    def test_users_dynamic(self, db_session):
        user1 = add_user(db_session, "user1", "email1")
        user2 = add_user(db_session, "user2", "email2")

        group = add_group(db_session)
        group.users.append(user1)
        group.users.append(user2)
        group_users = group.users_dynamic.all()

        assert group_users[0] == user1
        assert group_users[1] == user2

    def test_get(self, db_session):
        group1 = add_group(db_session, "group1")
        group = GroupService.get(group_id=group1.id, db_session=db_session)
        assert group.id == group1.id

    def test_all(self, db_session):
        group1 = add_group(db_session, "group1")
        group2 = add_group(db_session, "group2")

        all_groups = BaseService.all(Group, db_session=db_session).all()

        assert len(all_groups) == 2
        assert all_groups[0] == group1
        assert all_groups[1] == group2

    def test_user_paginator(self, db_session):
        user1 = add_user(db_session, "user1", "email1")
        user2 = add_user(db_session, "user2", "email2")

        group = add_group(db_session)
        group.users.append(user1)
        group.users.append(user2)
        users_count = len(group.users)
        get_params = {"foo": "bar", "baz": "xxx"}

        paginator = GroupService.get_user_paginator(
            group, 1, users_count, GET_params=get_params
        )

        assert paginator.page == 1
        assert paginator.first_item == 1
        assert paginator.last_item == 2
        assert paginator.items == [user1, user2]
        assert paginator.items == [user1, user2]
        assert paginator.items == [user1, user2]
        assert paginator.items == [user1, user2]

    def test_user_paginator_usernames(self, db_session):
        user1 = add_user(db_session, "user1", "email1")
        user2 = add_user(db_session, "user2", "email2")
        user3 = add_user(db_session, "user3", "email3")

        group = add_group(db_session)
        group.users.append(user1)
        group.users.append(user2)
        group.users.append(user3)

        # TODO: users count when filtering on names?
        paginator = GroupService.get_user_paginator(group, 1, user_ids=[1, 3])

        assert paginator.page == 1
        assert paginator.first_item == 1
        assert paginator.last_item == 2
        assert paginator.items == [user1, user3]
        assert paginator.item_count == 2
        assert paginator.page_count == 1
