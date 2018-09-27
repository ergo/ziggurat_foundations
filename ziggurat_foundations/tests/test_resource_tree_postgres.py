# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

import pprint

import pytest

from ziggurat_foundations.models.services.resource import ResourceService
from ziggurat_foundations.models.services.resource_tree import ResourceTreeService
from ziggurat_foundations.models.services.resource_tree_postgres import (
    ResourceTreeServicePostgreSQL,
)
from ziggurat_foundations.tests import add_resource, BaseTestCase, create_default_tree
from ziggurat_foundations.tests.conftest import not_postgres

tree_service = ResourceTreeService(ResourceTreeServicePostgreSQL)


class TestResources(BaseTestCase):
    def test_get(self, db_session):
        add_resource(db_session, 1, "root")
        resource = ResourceService.get(resource_id=1, db_session=db_session)
        assert resource.resource_id == 1
        assert resource.resource_name == "root"

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_root_nesting(self, db_session):
        root = create_default_tree(db_session)[0]

        result = tree_service.from_resource_deeper(
            root.resource_id, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree_struct = tree["children"][-1]
        pprint.pprint(tree_struct)
        assert tree_struct["node"].resource_id == -1
        l1_nodes = [n for n in tree_struct["children"].values()]
        a_node = tree_struct["children"][1]
        b_node = tree_struct["children"][2]
        ac_node = a_node["children"][7]
        l_a_nodes = [n for n in a_node["children"].values()]
        l_b_nodes = [n for n in b_node["children"].values()]
        l_ac_nodes = [n for n in ac_node["children"].values()]
        assert [n["node"].resource_id for n in l1_nodes] == [1, 2, 3, 10, 11]
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        assert [n["node"].resource_id for n in l_b_nodes] == [4]
        assert [n["node"].resource_id for n in l_ac_nodes] == [9]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_full_nesting(self, db_session):
        create_default_tree(db_session)

        result = tree_service.from_parent_deeper(db_session=db_session)
        tree_struct = tree_service.build_subtree_strut(result)
        pprint.pprint(tree_struct)
        root_nodes = [n for n in tree_struct["children"].values()]
        l1_nodes = [n for n in tree_struct["children"][-1]["children"].values()]
        assert [n["node"].resource_id for n in root_nodes] == [-1, -2, -3]
        assert [n["node"].resource_id for n in l1_nodes] == [1, 2, 3, 10, 11]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_branch_data_with_limit(self, db_session):
        create_default_tree(db_session)
        result = tree_service.from_resource_deeper(
            1, limit_depth=2, db_session=db_session
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"][1]
        pprint.pprint(tree_struct)
        assert tree_struct["node"].resource_id == 1
        l_a_nodes = [n for n in tree_struct["children"].values()]
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        assert len(tree_struct["children"][7]["children"].values()) == 0

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_branch_data_with_limit_from_parent(self, db_session):
        create_default_tree(db_session)
        result = tree_service.from_parent_deeper(
            1, limit_depth=2, db_session=db_session
        )
        tree_struct = tree_service.build_subtree_strut(result)
        pprint.pprint(tree_struct)
        l_a_nodes = [n for n in tree_struct["children"].values()]
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 6, 7, 8]
        elem = tree_struct["children"][7]["children"]
        assert len(elem[9]["children"].values()) == 0

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_going_up_hierarchy(self, db_session):
        create_default_tree(db_session=db_session)
        result = tree_service.path_upper(9, db_session=db_session)
        assert [r.resource_id for r in result] == [9, 7, 1, -1]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_up_on_same_branch(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(3, to_position=2, db_session=db_session)
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree = tree["children"][root.resource_id]
        pprint.pprint(tree)
        assert tree["children"][3]["node"].ordering == 2
        assert tree["children"][2]["node"].ordering == 3

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_up_on_same_branch_first(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(3, to_position=1, db_session=db_session)
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree = tree["children"][root.resource_id]
        pprint.pprint(tree)
        assert tree["children"][3]["node"].ordering == 1
        assert tree["children"][1]["node"].ordering == 2
        assert tree["children"][2]["node"].ordering == 3
        assert tree["children"][10]["node"].ordering == 4
        assert tree["children"][11]["node"].ordering == 5

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_down_on_same_branch(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(1, to_position=3, db_session=db_session)
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree = tree["children"][root.resource_id]
        pprint.pprint(tree)
        assert tree["children"][2]["node"].ordering == 1
        assert tree["children"][3]["node"].ordering == 2
        assert tree["children"][1]["node"].ordering == 3

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_down_on_same_branch_witn_new_parent_set(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(
            1, to_position=3, new_parent_id=-1, db_session=db_session
        )
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree = tree["children"][root.resource_id]
        pprint.pprint(tree)
        assert tree["children"][2]["node"].ordering == 1
        assert tree["children"][3]["node"].ordering == 2
        assert tree["children"][1]["node"].ordering == 3

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_down_on_same_branch_last(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(1, to_position=5, db_session=db_session)
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree = tree["children"][root.resource_id]
        pprint.pprint(tree)
        assert tree["children"][2]["node"].ordering == 1
        assert tree["children"][3]["node"].ordering == 2
        assert tree["children"][10]["node"].ordering == 3
        assert tree["children"][11]["node"].ordering == 4
        assert tree["children"][1]["node"].ordering == 5

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_down_on_same_branch_last_on_root(self, db_session):
        create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(-2, to_position=3, db_session=db_session)
        result = tree_service.from_parent_deeper(
            None, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        pprint.pprint(tree)
        assert tree["children"][-1]["node"].ordering == 1
        assert tree["children"][-3]["node"].ordering == 2
        assert tree["children"][-2]["node"].ordering == 3

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_before_1_on_same_branch(self, db_session):
        from ziggurat_foundations.exc import ZigguratResourceOutOfBoundaryException

        create_default_tree(db_session=db_session)
        with pytest.raises(ZigguratResourceOutOfBoundaryException):
            tree_service.move_to_position(3, to_position=0, db_session=db_session)

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_after_last_on_same_branch(self, db_session):
        from ziggurat_foundations.exc import ZigguratResourceOutOfBoundaryException

        root = create_default_tree(db_session=db_session)[0]
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree = tree["children"][root.resource_id]
        pprint.pprint(tree)
        with pytest.raises(ZigguratResourceOutOfBoundaryException):
            tree_service.move_to_position(3, to_position=6, db_session=db_session)

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_to_same_position(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(1, to_position=1, db_session=db_session)
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)["children"][root.resource_id]
        assert tree["children"][1]["node"].ordering == 1
        assert tree["children"][2]["node"].ordering == 2
        assert tree["children"][3]["node"].ordering == 3

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_inside_itself(self, db_session):
        from ziggurat_foundations.exc import ZigguratResourceTreePathException

        create_default_tree(db_session=db_session)
        with pytest.raises(ZigguratResourceTreePathException):
            tree_service.move_to_position(
                1, to_position=1, new_parent_id=6, db_session=db_session
            )

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_wrong_new_parent(self, db_session):
        from ziggurat_foundations.exc import ZigguratResourceTreeMissingException

        create_default_tree(db_session=db_session)
        with pytest.raises(ZigguratResourceTreeMissingException):
            tree_service.move_to_position(
                1, to_position=1, new_parent_id=-6, db_session=db_session
            )

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_to_same_parent(self, db_session):
        root = create_default_tree(db_session=db_session)[0]
        tree_service.move_to_position(
            1, 1, new_parent_id=root.resource_id, db_session=db_session
        )
        result = tree_service.from_resource_deeper(
            root.resource_id, limit_depth=2, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)["children"][root.resource_id]
        assert tree["children"][1]["node"].ordering == 1
        assert tree["children"][2]["node"].ordering == 2
        assert tree["children"][3]["node"].ordering == 3

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_on_different_branch_with_siblings(self, db_session):
        create_default_tree(db_session)
        tree_service.move_to_position(
            6, new_parent_id=-1, to_position=1, db_session=db_session
        )

        result = tree_service.from_resource_deeper(
            -1, limit_depth=3, db_session=db_session
        )
        tree = tree_service.build_subtree_strut(result)
        tree_struct = tree["children"][-1]
        pprint.pprint(tree_struct)
        l_r_nodes = [n for n in tree_struct["children"].values()]
        check_values = [6, 1, 2, 3, 10, 11]
        assert [n["node"].resource_id for n in l_r_nodes] == check_values
        l_a_nodes = [n for n in tree_struct["children"][1]["children"].values()]
        pprint.pprint(l_a_nodes)
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 7, 8]
        assert [n["node"].ordering for n in l_a_nodes] == [1, 2, 3]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_after_last_on_different_branch(self, db_session):
        from ziggurat_foundations.exc import ZigguratResourceOutOfBoundaryException

        create_default_tree(db_session=db_session)
        with pytest.raises(ZigguratResourceOutOfBoundaryException):
            tree_service.move_to_position(
                4, new_parent_id=-1, to_position=7, db_session=db_session
            )

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_to_first_on_different_branch(self, db_session):
        create_default_tree(db_session)
        tree_service.move_to_position(
            4, new_parent_id=1, to_position=1, db_session=db_session
        )

        result = tree_service.from_resource_deeper(
            1, limit_depth=2, db_session=db_session
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"][1]
        pprint.pprint(tree_struct)
        l_a_nodes = [n for n in tree_struct["children"].values()]
        assert [n["node"].resource_id for n in l_a_nodes] == [4, 5, 6, 7, 8]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_to_middle_on_different_branch(self, db_session):
        create_default_tree(db_session)
        tree_service.move_to_position(
            4, new_parent_id=1, to_position=3, db_session=db_session
        )

        result = tree_service.from_resource_deeper(
            1, limit_depth=2, db_session=db_session
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"][1]
        pprint.pprint(tree_struct)
        l_a_nodes = [n for n in tree_struct["children"].values()]
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 6, 4, 7, 8]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_to_last_on_different_branch(self, db_session):
        create_default_tree(db_session)
        tree_service.move_to_position(
            4, new_parent_id=1, to_position=5, db_session=db_session
        )

        result = tree_service.from_resource_deeper(
            1, limit_depth=2, db_session=db_session
        )
        tree_struct = tree_service.build_subtree_strut(result)["children"][1]
        pprint.pprint(tree_struct)
        l_a_nodes = [n for n in tree_struct["children"].values()]
        assert [n["node"].resource_id for n in l_a_nodes] == [5, 6, 7, 8, 4]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_to_first_on_root_branch(self, db_session):
        create_default_tree(db_session)
        tree_service.move_to_position(
            4, new_parent_id=None, to_position=1, db_session=db_session
        )

        result = tree_service.from_parent_deeper(parent_id=None, db_session=db_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        r_nodes = [n for n in tree_struct.values()]
        assert [n["node"].resource_id for n in r_nodes] == [4, -1, -2, -3]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    def test_move_from_root_deeper(self, db_session):
        create_default_tree(db_session)
        tree_service.move_to_position(
            -2, new_parent_id=1, to_position=1, db_session=db_session
        )

        result = tree_service.from_parent_deeper(parent_id=None, db_session=db_session)
        tree_struct = tree_service.build_subtree_strut(result)["children"]
        pprint.pprint(tree_struct)
        r_nodes = [n for n in tree_struct[-1]["children"][1]["children"].values()]
        assert [n["node"].resource_id for n in r_nodes] == [-2, 5, 6, 7, 8]
        assert list(tree_struct.keys()) == [-1, -3]
        assert [n["node"].ordering for n in tree_struct.values()] == [1, 2]

    @pytest.mark.skipif(not_postgres, reason="requires postgres")
    @pytest.mark.parametrize(
        "resource_id, expected_ids, expected_order",
        [
            (1, [-1, 2, 4, 3, 10, 11, -2, -3], None),
            (9, [-1, 1, 5, 6, 7, 8, 2, 4, 3, 10, 11, -2, -3], None),
            (12, [-1, 1, 5, 6, 7, 9, 8, 2, 4, 3, 10, 11, -2, -3], None),
            (-1, [-2, -3], [1, 2]),
        ],
    )
    def test_delete_branches(
        self, db_session, resource_id, expected_ids, expected_order
    ):
        create_default_tree(db_session)
        tree_service.delete_branch(resource_id, db_session=db_session)

        result = tree_service.from_parent_deeper(parent_id=None, db_session=db_session)
        row_ids = [r.Resource.resource_id for r in result]
        ordering = [r.Resource.ordering for r in result]
        assert row_ids == expected_ids
        if expected_order:
            assert ordering == expected_order
