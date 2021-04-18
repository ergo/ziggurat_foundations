# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import OrderedDict

import sqlalchemy as sa

from ziggurat_foundations.utils import noop
from ziggurat_foundations.exc import (
    ZigguratResourceTreeMissingException,
    ZigguratResourceTreePathException,
    ZigguratResourceOutOfBoundaryException,
)
from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services.resource import ResourceService

__all__ = ["ResourceTreeServicePostgreSQL"]


class ResourceTreeServicePostgreSQL(object):
    model = None

    @classmethod
    def from_resource_deeper(
        cls, resource_id=None, limit_depth=1000000, db_session=None, *args, **kwargs
    ):
        """
        This returns you subtree of ordered objects relative
        to the start resource_id (currently only implemented in postgresql)

        :param resource_id:
        :param limit_depth:
        :param db_session:
        :return:
        """
        tablename = cls.model.__table__.name
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 AS depth, LPAD(res.ordering::CHARACTER VARYING, 7, '0') AS sorting,
                    res.resource_id::CHARACTER VARYING AS path
                    FROM {tablename} AS res WHERE res.resource_id = :resource_id
                  UNION ALL
                    SELECT res_u.*, depth+1 AS depth,
                    (st.sorting::CHARACTER VARYING || '/' || LPAD(res_u.ordering::CHARACTER VARYING, 7, '0') ) AS sorting,
                    (st.path::CHARACTER VARYING || '/' || res_u.resource_id::CHARACTER VARYING ) AS path
                    FROM {tablename} res_u, subtree st
                    WHERE res_u.parent_id = st.resource_id
            )
            SELECT * FROM subtree WHERE depth<=:depth ORDER BY sorting;
        """.format(
            tablename=tablename
        )  # noqa
        db_session = get_db_session(db_session)
        text_obj = sa.text(raw_q)
        query = db_session.query(cls.model, sa.column("depth"), sa.column("sorting"), sa.column("path"))
        query = query.from_statement(text_obj)
        query = query.params(resource_id=resource_id, depth=limit_depth)
        return query

    @classmethod
    def delete_branch(cls, resource_id=None, db_session=None, *args, **kwargs):
        """
        This deletes whole branch with children starting from resource_id

        :param resource_id:
        :param db_session:
        :return:
        """
        tablename = cls.model.__table__.name

        # lets lock rows to prevent bad tree states
        resource = ResourceService.lock_resource_for_update(
            resource_id=resource_id, db_session=db_session
        )
        parent_id = resource.parent_id
        ordering = resource.ordering
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.resource_id
                    FROM {tablename} AS res WHERE res.resource_id = :resource_id
                  UNION ALL
                    SELECT res_u.resource_id
                    FROM {tablename} res_u, subtree st
                    WHERE res_u.parent_id = st.resource_id
            )
            DELETE FROM resources where resource_id in (select * from subtree);
        """.format(
            tablename=tablename
        )  # noqa
        db_session = get_db_session(db_session)
        text_obj = sa.text(raw_q)
        db_session.execute(text_obj, params={"resource_id": resource_id})
        cls.shift_ordering_down(parent_id, ordering, db_session=db_session)
        return True

    @classmethod
    def from_parent_deeper(
        cls, parent_id=None, limit_depth=1000000, db_session=None, *args, **kwargs
    ):
        """
        This returns you subtree of ordered objects relative
        to the start parent_id (currently only implemented in postgresql)

        :param resource_id:
        :param limit_depth:
        :param db_session:
        :return:
        """

        if parent_id:
            limiting_clause = "res.parent_id = :parent_id"
        else:
            limiting_clause = "res.parent_id is null"
        tablename = cls.model.__table__.name
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 AS depth, LPAD(res.ordering::CHARACTER VARYING, 7, '0') AS sorting,
                    res.resource_id::CHARACTER VARYING AS path
                    FROM {tablename} AS res WHERE {limiting_clause}
                  UNION ALL
                    SELECT res_u.*, depth+1 AS depth,
                    (st.sorting::CHARACTER VARYING || '/' || LPAD(res_u.ordering::CHARACTER VARYING, 7, '0') ) AS sorting,
                    (st.path::CHARACTER VARYING || '/' || res_u.resource_id::CHARACTER VARYING ) AS path
                    FROM {tablename} res_u, subtree st
                    WHERE res_u.parent_id = st.resource_id
            )
            SELECT * FROM subtree WHERE depth<=:depth ORDER BY sorting;
        """.format(
            tablename=tablename, limiting_clause=limiting_clause
        )  # noqa
        db_session = get_db_session(db_session)
        text_obj = sa.text(raw_q)
        query = db_session.query(cls.model, sa.column("depth"), sa.column("sorting"), sa.column("path"))
        query = query.from_statement(text_obj)
        query = query.params(parent_id=parent_id, depth=limit_depth)
        return query

    @classmethod
    def build_subtree_strut(cls, result, *args, **kwargs):
        """
        Returns a dictionary in form of
        {node:Resource, children:{node_id: Resource}}

        :param result:
        :return:
        """
        items = list(result)
        root_elem = {"node": None, "children": OrderedDict()}
        if len(items) == 0:
            return root_elem
        for _, node in enumerate(items):
            node_res = getattr(node, cls.model.__name__)
            new_elem = {"node": node_res, "children": OrderedDict()}
            path = list(map(int, node.path.split("/")))
            parent_node = root_elem
            normalized_path = path[:-1]
            if normalized_path:
                for path_part in normalized_path:
                    parent_node = parent_node["children"][path_part]
            parent_node["children"][new_elem["node"].resource_id] = new_elem
        return root_elem

    @classmethod
    def path_upper(
        cls, object_id, limit_depth=1000000, db_session=None, *args, **kwargs
    ):
        """
        This returns you path to root node starting from object_id
            currently only for postgresql

        :param object_id:
        :param limit_depth:
        :param db_session:
        :return:
        """
        tablename = cls.model.__table__.name
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 as depth FROM {tablename} res
                    WHERE res.resource_id = :resource_id
                  UNION ALL
                    SELECT res_u.*, depth+1 as depth
                    FROM {tablename} res_u, subtree st
                    WHERE res_u.resource_id = st.parent_id
            )
            SELECT * FROM subtree WHERE depth<=:depth;
        """.format(
            tablename=tablename
        )
        db_session = get_db_session(db_session)
        q = (
            db_session.query(cls.model)
            .from_statement(sa.text(raw_q))
            .params(resource_id=object_id, depth=limit_depth)
        )
        return q

    @classmethod
    def move_to_position(
        cls,
        resource_id,
        to_position,
        new_parent_id=noop,
        db_session=None,
        *args,
        **kwargs
    ):
        """
        Moves node to new location in the tree

        :param resource_id: resource to move
        :param to_position: new position
        :param new_parent_id: new parent id
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        # lets lock rows to prevent bad tree states
        resource = ResourceService.lock_resource_for_update(
            resource_id=resource_id, db_session=db_session
        )
        ResourceService.lock_resource_for_update(
            resource_id=resource.parent_id, db_session=db_session
        )
        same_branch = False

        # reset if parent is same as old
        if new_parent_id == resource.parent_id:
            new_parent_id = noop

        if new_parent_id is not noop:
            cls.check_node_parent(resource_id, new_parent_id, db_session=db_session)
        else:
            same_branch = True

        if new_parent_id is noop:
            # it is not guaranteed that parent exists
            parent_id = resource.parent_id if resource else None
        else:
            parent_id = new_parent_id

        cls.check_node_position(
            parent_id, to_position, on_same_branch=same_branch, db_session=db_session
        )
        # move on same branch
        if new_parent_id is noop:
            order_range = list(sorted((resource.ordering, to_position)))
            move_down = resource.ordering > to_position

            query = db_session.query(cls.model)
            query = query.filter(cls.model.parent_id == parent_id)
            query = query.filter(cls.model.ordering.between(*order_range))
            if move_down:
                query.update(
                    {cls.model.ordering: cls.model.ordering + 1},
                    synchronize_session=False,
                )
            else:
                query.update(
                    {cls.model.ordering: cls.model.ordering - 1},
                    synchronize_session=False,
                )
            db_session.flush()
            db_session.expire(resource)
            resource.ordering = to_position
        # move between branches
        else:
            cls.shift_ordering_down(
                resource.parent_id, resource.ordering, db_session=db_session
            )
            cls.shift_ordering_up(new_parent_id, to_position, db_session=db_session)
            db_session.expire(resource)
            resource.parent_id = new_parent_id
            resource.ordering = to_position
            db_session.flush()
        return True

    @classmethod
    def shift_ordering_down(cls, parent_id, position, db_session=None, *args, **kwargs):
        """
        Shifts ordering to "close gaps" after node deletion or being moved
        to another branch, begins the shift from given position

        :param parent_id:
        :param position:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model)
        query = query.filter(cls.model.parent_id == parent_id)
        query = query.filter(cls.model.ordering >= position)
        query.update(
            {cls.model.ordering: cls.model.ordering - 1}, synchronize_session=False
        )
        db_session.flush()

    @classmethod
    def shift_ordering_up(cls, parent_id, position, db_session=None, *args, **kwargs):
        """
        Shifts ordering to "open a gap" for node insertion,
        begins the shift from given position

        :param parent_id:
        :param position:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        query = db_session.query(cls.model)
        query = query.filter(cls.model.parent_id == parent_id)
        query = query.filter(cls.model.ordering >= position)
        query.update(
            {cls.model.ordering: cls.model.ordering + 1}, synchronize_session=False
        )
        db_session.flush()

    @classmethod
    def set_position(cls, resource_id, to_position, db_session=None, *args, **kwargs):
        """
        Sets node position for new node in the tree

        :param resource_id: resource to move
        :param to_position: new position
        :param db_session:
        :return:def count_children(cls, resource_id, db_session=None):
        """
        db_session = get_db_session(db_session)
        # lets lock rows to prevent bad tree states
        resource = ResourceService.lock_resource_for_update(
            resource_id=resource_id, db_session=db_session
        )
        cls.check_node_position(
            resource.parent_id, to_position, on_same_branch=True, db_session=db_session
        )
        cls.shift_ordering_up(resource.parent_id, to_position, db_session=db_session)
        db_session.flush()
        db_session.expire(resource)
        resource.ordering = to_position
        return True

    @classmethod
    def check_node_parent(
        cls, resource_id, new_parent_id, db_session=None, *args, **kwargs
    ):
        """
        Checks if parent destination is valid for node

        :param resource_id:
        :param new_parent_id:
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        new_parent = ResourceService.lock_resource_for_update(
            resource_id=new_parent_id, db_session=db_session
        )
        # we are not moving to "root" so parent should be found
        if not new_parent and new_parent_id is not None:
            raise ZigguratResourceTreeMissingException("New parent node not found")
        else:
            result = cls.path_upper(new_parent_id, db_session=db_session)
            path_ids = [r.resource_id for r in result]
            if resource_id in path_ids:
                raise ZigguratResourceTreePathException(
                    "Trying to insert node into itself"
                )

    @classmethod
    def count_children(cls, resource_id, db_session=None, *args, **kwargs):
        """
        Counts children of resource node

        :param resource_id:
        :param db_session:
        :return:
        """
        query = db_session.query(cls.model.resource_id)
        query = query.filter(cls.model.parent_id == resource_id)
        return query.count()

    @classmethod
    def check_node_position(
        cls, parent_id, position, on_same_branch, db_session=None, *args, **kwargs
    ):
        """
        Checks if node position for given parent is valid, raises exception if
        this is not the case

        :param parent_id:
        :param position:
        :param on_same_branch: indicates that we are checking same branch
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        if not position or position < 1:
            raise ZigguratResourceOutOfBoundaryException(
                "Position is lower than {}", value=1
            )
        item_count = cls.count_children(parent_id, db_session=db_session)
        max_value = item_count if on_same_branch else item_count + 1
        if position > max_value:
            raise ZigguratResourceOutOfBoundaryException(
                "Maximum resource ordering is {}", value=max_value
            )
