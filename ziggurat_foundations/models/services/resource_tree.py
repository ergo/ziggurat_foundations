# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from ziggurat_foundations.utils import noop

__all__ = ["ResourceTreeService"]


class ResourceTreeService(object):
    model = None

    def __init__(self, service_cls):
        service_cls.model = self.model
        self.service = service_cls

    def from_resource_deeper(
        self, resource_id=None, limit_depth=1000000, db_session=None, *args, **kwargs
    ):
        """
        This returns you subtree of ordered objects relative
        to the start resource_id (currently only implemented in postgresql)

        :param resource_id:
        :param limit_depth:
        :param db_session:
        :return:
        """
        return self.service.from_resource_deeper(
            resource_id=resource_id,
            limit_depth=limit_depth,
            db_session=db_session,
            *args,
            **kwargs
        )

    def delete_branch(self, resource_id=None, db_session=None, *args, **kwargs):
        """
        This deletes whole branch with children starting from resource_id

        :param resource_id:
        :param db_session:
        :return:
        """
        return self.service.delete_branch(
            resource_id=resource_id, db_session=db_session, *args, **kwargs
        )

    def from_parent_deeper(
        self, parent_id=None, limit_depth=1000000, db_session=None, *args, **kwargs
    ):
        """
        This returns you subtree of ordered objects relative
        to the start parent_id (currently only implemented in postgresql)

        :param resource_id:
        :param limit_depth:
        :param db_session:
        :return:
        """
        return self.service.from_parent_deeper(
            parent_id=parent_id,
            limit_depth=limit_depth,
            db_session=db_session,
            *args,
            **kwargs
        )

    def build_subtree_strut(self, result, *args, **kwargs):
        """
        Returns a dictionary in form of
        {node:Resource, children:{node_id: Resource}}

        :param result:
        :return:
        """
        return self.service.build_subtree_strut(result=result, *args, **kwargs)

    def path_upper(
        self, object_id, limit_depth=1000000, db_session=None, *args, **kwargs
    ):
        """
        This returns you path to root node starting from object_id
            currently only for postgresql

        :param object_id:
        :param limit_depth:
        :param db_session:
        :return:
        """
        return self.service.path_upper(
            object_id=object_id,
            limit_depth=limit_depth,
            db_session=db_session,
            *args,
            **kwargs
        )

    def move_to_position(
        self,
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
        return self.service.move_to_position(
            resource_id=resource_id,
            to_position=to_position,
            new_parent_id=new_parent_id,
            db_session=db_session,
            *args,
            **kwargs
        )

    def shift_ordering_down(
        self, parent_id, position, db_session=None, *args, **kwargs
    ):
        """
        Shifts ordering to "close gaps" after node deletion or being moved
        to another branch, begins the shift from given position

        :param parent_id:
        :param position:
        :param db_session:
        :return:
        """
        return self.service.shift_ordering_down(
            parent_id=parent_id,
            position=position,
            db_session=db_session,
            *args,
            **kwargs
        )

    def shift_ordering_up(self, parent_id, position, db_session=None, *args, **kwargs):
        """
        Shifts ordering to "open a gap" for node insertion,
        begins the shift from given position

        :param parent_id:
        :param position:
        :param db_session:
        :return:
        """
        return self.service.shift_ordering_up(
            parent_id=parent_id,
            position=position,
            db_session=db_session,
            *args,
            **kwargs
        )

    def set_position(self, resource_id, to_position, db_session=None, *args, **kwargs):
        """
        Sets node position for new node in the tree

        :param resource_id: resource to move
        :param to_position: new position
        :param db_session:
        :return:def count_children(cls, resource_id, db_session=None):
        """
        return self.service.set_position(
            resource_id=resource_id,
            to_position=to_position,
            db_session=db_session,
            *args,
            **kwargs
        )

    def check_node_parent(
        self, resource_id, new_parent_id, db_session=None, *args, **kwargs
    ):
        """
        Checks if parent destination is valid for node

        :param resource_id:
        :param new_parent_id:
        :param db_session:
        :return:
        """
        return self.service.check_node_parent(
            resource_id=resource_id,
            new_parent_id=new_parent_id,
            db_session=db_session,
            *args,
            **kwargs
        )

    def count_children(self, resource_id, db_session=None, *args, **kwargs):
        """
        Counts children of resource node

        :param resource_id:
        :param db_session:
        :return:
        """
        return self.service.count_children(
            resource_id=resource_id, db_session=db_session, *args, **kwargs
        )

    def check_node_position(
        self, parent_id, position, on_same_branch, db_session=None, *args, **kwargs
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
        return self.service.check_node_position(
            parent_id=parent_id,
            position=position,
            on_same_branch=on_same_branch,
            db_session=db_session,
            *args,
            **kwargs
        )
