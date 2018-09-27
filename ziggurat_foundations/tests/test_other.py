# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

from ziggurat_foundations.models.services.external_identity import (
    ExternalIdentityService,
)
from ziggurat_foundations.tests import add_user, add_resource, BaseTestCase
from ziggurat_foundations.tests.conftest import (
    UserGroup,
    ExternalIdentity,
    GroupResourcePermission,
)


class TestUserGroup(BaseTestCase):
    def test_repr(self, db_session):
        user_group = UserGroup(user_id=1, group_id=1)

        assert repr(user_group) == "<UserGroup: g:1, u:1>"


class TestGroupResourcePermission(BaseTestCase):
    def test_repr(self, db_session):
        group_resource_perm = GroupResourcePermission(
            group_id=1, resource_id=1, perm_name="perm"
        )
        assert repr(group_resource_perm) == "<GroupResourcePermission: g:1, perm, r:1>"


class TestAddResource(BaseTestCase):
    def test_pkey(self, db_session):
        resource = add_resource(db_session, 99, "some random name")
        assert resource.resource_id == 99

    def test_nopkey(self, db_session):
        resource = add_resource(db_session, None, "some random name")
        assert resource.resource_id == 1


class TestExternalIdentity(BaseTestCase):
    def test_by_external_id_and_provider(self, db_session):
        user = add_user(db_session)
        identity = ExternalIdentity(
            external_user_name="foo", external_id="foo", provider_name="facebook"
        )
        user.external_identities.append(identity)
        # db_session.flush()
        found = ExternalIdentityService.by_external_id_and_provider(
            provider_name="facebook", external_id="foo", db_session=db_session
        )
        assert identity == found

    def test_get(self, db_session):
        user = add_user(db_session)
        identity = ExternalIdentity(
            external_user_name="foo", external_id="foo", provider_name="facebook"
        )
        user.external_identities.append(identity)
        db_session.flush()
        found = ExternalIdentityService.get(
            provider_name="facebook",
            external_id="foo",
            local_user_id=user.id,
            db_session=db_session,
        )
        assert identity == found

    def test_user_by_external_id_and_provider(self, db_session):
        user = add_user(db_session)
        identity = ExternalIdentity(
            external_user_name="foo", external_id="foo", provider_name="facebook"
        )
        user.external_identities.append(identity)
        # db_session.flush()
        found = ExternalIdentityService.user_by_external_id_and_provider(
            provider_name="facebook", external_id="foo", db_session=db_session
        )
        assert user == found


class TestUtils(BaseTestCase):
    def test_permission_to_04_acls(self, db_session):
        pass
