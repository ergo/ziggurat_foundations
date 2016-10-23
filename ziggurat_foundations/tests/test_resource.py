# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals
import pytest

from ziggurat_foundations.tests import (
    add_resource, BaseTestCase)
from ziggurat_foundations.tests.conftest import Resource, not_postgres
from ziggurat_foundations.models.services.resource import ResourceService


def create_default_tree(db_session):
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
    return root


class TestResources(BaseTestCase):
    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_root_nesting(self, db_session):
        root = create_default_tree(db_session)

        result = ResourceService.subtree_deeper(root.resource_id,
                                                db_session=db_session)
        tree_struct = ResourceService.build_subtree_strut(result)

        assert tree_struct['node'].resource_id == -1
        l1_nodes = [n for n in tree_struct['children'].values()]
        a_node = tree_struct['children'][1];
        b_node = tree_struct['children'][2];
        ac_node = a_node['children'][7]
        l_a_nodes = [n for n in a_node['children'].values()]
        l_b_nodes = [n for n in b_node['children'].values()]
        l_ac_nodes = [n for n in ac_node['children'].values()]
        assert [n['node'].resource_id for n in l1_nodes] == [1, 2, 3]
        assert [n['node'].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        assert [n['node'].resource_id for n in l_b_nodes] == [4]
        assert [n['node'].resource_id for n in l_ac_nodes] == [9]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_branch_data_with_limit(self, db_session):
        create_default_tree(db_session)
        result = ResourceService.subtree_deeper(1, limit_depth=2,
                                                db_session=db_session)
        tree_struct = ResourceService.build_subtree_strut(result)
        assert tree_struct['node'].resource_id == 1
        l_a_nodes = [n for n in tree_struct['children'].values()]
        assert [n['node'].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        assert len(tree_struct['children'][7]['children'].values()) == 0

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_going_up(self, db_session):
        root = create_default_tree(db_session=db_session)
        result = ResourceService.path_upper(9, db_session=db_session)
        assert [r.resource_id for r in result] == [9, 7, 1, -1]
