from __future__ import unicode_literals

from ziggurat_foundations import noparent

__all__ = ['ResourceTreeService']


class ResourceTreeService(object):
    def __init__(self, service_cls):
        service_cls.model = self.model
        self.service = service_cls


    def from_resource_deeper(self, resource_id=None, limit_depth=1000000,
                             db_session=None, *args, **kwargs):
        return self.service.from_resource_deeper(
            resource_id=resource_id, limit_depth=limit_depth,
            db_session=db_session, *args, **kwargs)

    def delete_branch(self, resource_id=None, db_session=None,
                      *args, **kwargs):
        return self.service.delete_branch(
            resource_id=resource_id, db_session=db_session, *args, **kwargs)

    def from_parent_deeper(self, parent_id=None, limit_depth=1000000,
                           db_session=None, *args, **kwargs):
        return self.service.from_parent_deeper(
            parent_id=parent_id, limit_depth=limit_depth,
            db_session=db_session, *args, **kwargs)

    def build_subtree_strut(self, result, *args, **kwargs):
        return self.service.build_subtree_strut(result=result, *args, **kwargs)

    def path_upper(self, object_id, limit_depth=1000000, db_session=None, *args,
                   **kwargs):
        return self.service.path_upper(
            object_id=object_id, limit_depth=limit_depth, db_session=db_session,
            *args, **kwargs)

    def move_to_position(self, resource_id, to_position, new_parent_id=noparent,
                         db_session=None, *args, **kwargs):
        return self.service.move_to_position(
            resource_id=resource_id, to_position=to_position,
            new_parent_id=new_parent_id, db_session=db_session, *args, **kwargs)

    def shift_ordering_down(self, parent_id, position, db_session=None,
                            *args, **kwargs):
        return self.service.shift_ordering_down(
            parent_id=parent_id, position=position, db_session=db_session,
            *args, **kwargs)

    def shift_ordering_up(self, parent_id, position, db_session=None,
                          *args, **kwargs):
        return self.service.shift_ordering_up(
            parent_id=parent_id, position=position, db_session=db_session,
            *args, **kwargs)

    def set_position(self, resource_id, to_position, db_session=None, *args,
                     **kwargs):
        return self.service.set_position(
            resource_id=resource_id, to_position=to_position,
            db_session=db_session, *args, **kwargs)

    def check_node_parent(self, resource_id, new_parent_id, db_session=None,
                          *args, **kwargs):
        return self.service.check_node_parent(
            resource_id=resource_id, new_parent_id=new_parent_id,
            db_session=db_session, *args, **kwargs)

    def count_children(self, resource_id, db_session=None, *args, **kwargs):
        return self.service.count_children(self, resource_id=resource_id,
                                           db_session=db_session, *args,
                                           **kwargs)

    def check_node_position(
            self, parent_id, position, on_same_branch, db_session=None,
            *args, **kwargs):
        return self.service.check_node_position(
            parent_id=parent_id, position=position,
            on_same_branch=on_same_branch, db_session=db_session, *args,
            **kwargs)
