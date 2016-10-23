# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals
import pytest

from ziggurat_foundations.permissions import PermissionTuple, ALL_PERMISSIONS

from ziggurat_foundations.tests import (
    add_user, check_one_in_other, add_resource, add_resource_b, add_group,
    BaseTestCase)
from ziggurat_foundations.tests.conftest import Resource
from ziggurat_foundations.models.services.resource import ResourceService


class TestResources(BaseTestCase):
    def test_nesting(self, db_session):
        root = add_resource(
            db_session, -1, 'root', ordering=1)
        res_a = add_resource(
            db_session, 1, 'a', parent_id=root.resource_id, ordering=2)
        res_aa = add_resource(
            db_session, 5, 'aa', parent_id=res_a.resource_id, ordering=1)
        res_ab = add_resource(
            db_session, 6, 'ab', parent_id=res_a.resource_id, ordering=2)
        res_ac = add_resource(
            db_session, 7, 'ac', parent_id=res_a.resource_id, ordering=3)
        res_aca = add_resource(
            db_session, 9, 'aca', parent_id=res_ac.resource_id, ordering=1)
        res_ad = add_resource(
            db_session, 8, 'ad', parent_id=res_a.resource_id, ordering=4)
        res_b = add_resource(
            db_session, 2, 'b', parent_id=root.resource_id, ordering=3)
        res_ba = add_resource(
            db_session, 4, 'ba', parent_id=res_b.resource_id, ordering=1)
        res_c = add_resource(
            db_session, 3, 'c', parent_id=root.resource_id, ordering=4)

        result = ResourceService.subtree_deeper(root.resource_id,
                                                db_session=db_session)
        tree_struct = ResourceService.build_subtree_strut(result)
