import sqlalchemy as sa
from . import ModelManager
from ...utils import get_db_session
from ...permissions import (ANY_PERMISSION,
                            ALL_PERMISSIONS,
                            PermissionTuple,
                            resource_permissions_for_users)


class ResourceManager(ModelManager):
    def perms_for_user(self, user, db_session=None):
        """ returns all permissions that given user has for this resource
            from groups and directly set ones too"""
        db_session = get_db_session(db_session, self)
        query = db_session.query(
            self._ziggurat_models.GroupResourcePermission.group_id.label('owner_id'),
            self._ziggurat_models.GroupResourcePermission.perm_name,
            sa.literal('group').label('type'))
        query = query.filter(self._ziggurat_models.GroupResourcePermission.group_id.in_(
            [gr.id for gr in user.groups]
        )
        )
        query = query.filter(self._ziggurat_models.GroupResourcePermission.resource_id ==
                             self.resource_id)

        query2 = db_session.query(
            self._ziggurat_models.UserResourcePermission.user_id.label('owner_id'),
            self._ziggurat_models.UserResourcePermission.perm_name,
            sa.literal('user').label('type'))
        query2 = query2.filter(self._ziggurat_models.UserResourcePermission.user_id ==
                               user.id)
        query2 = query2.filter(self._ziggurat_models.UserResourcePermission.resource_id ==
                               self.resource_id)
        query = query.union(query2)

        groups_dict = dict([(g.id, g) for g in user.groups])
        perms = [PermissionTuple(user,
                                 row.perm_name,
                                 row.type,
                                 groups_dict.get(row.owner_id) if
                                 row.type == 'group' else None,
                                 self, False, True) for row in query]

        # include all perms if user is the owner of this resource
        if self.owner_user_id == user.id:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'user',
                                         None, self, True, True))
        groups_dict = dict([(g.id, g) for g in user.groups])
        if self.owner_group_id in groups_dict:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                         groups_dict.get(self.owner_group_id),
                                         self, True, True))

        return perms

    def direct_perms_for_user(self, user, db_session=None):
        """ returns permissions that given user has for this resource
            without ones inherited from groups that user belongs to"""
        db_session = get_db_session(db_session, self)
        query = db_session.query(self._ziggurat_models.UserResourcePermission.user_id,
                                 self._ziggurat_models.UserResourcePermission.perm_name)
        query = query.filter(self._ziggurat_models.UserResourcePermission.user_id ==
                             user.id)
        query = query.filter(self._ziggurat_models.UserResourcePermission.resource_id ==
                             self.resource_id)

        perms = [PermissionTuple(user,
                                 row.perm_name,
                                 'user',
                                 None,
                                 self, False, True) for row in query]

        # include all perms if user is the owner of this resource
        if self.owner_user_id == user.id:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'user',
                                         None, self, True))
        return perms

    def group_perms_for_user(self, user, db_session=None):
        """ returns permissions that given user has for this resource
            that are inherited from groups """
        db_session = get_db_session(db_session, self)
        perms = resource_permissions_for_users(self, ANY_PERMISSION,
                                               resource_ids=[self.resource_id],
                                               user_ids=[user.id],
                                               db_session=None)
        perms = [p for p in perms if p.type == 'group']
        # include all perms if user is the owner of this resource
        groups_dict = dict([(g.id, g) for g in user.groups])
        if self.owner_group_id in groups_dict:
            perms.append(PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                         groups_dict.get(self.owner_group_id),
                                         self, True, True))
        return perms

    def users_for_perm(self, perm_name, user_ids=None, group_ids=None,
                       limit_group_permissions=False, skip_group_perms=False,
                       db_session=None):
        """ return PermissionTuples for users AND groups that have given
        permission for the resource, perm_name is __any_permission__ then
        users with any permission will be listed
        user_ids - limits the permissions to specific user ids,
        group_ids - limits the permissions to specific group ids,
        """
        db_session = get_db_session(db_session, self)
        users_perms = resource_permissions_for_users(self, [perm_name],
                                                     [self.resource_id],
                                                     user_ids=user_ids,
                                                     group_ids=group_ids,
                                                     limit_group_permissions=limit_group_permissions,
                                                     skip_group_perms=skip_group_perms,
                                                     db_session=db_session)
        if self.owner_user_id:
            users_perms.append(
                PermissionTuple(self.owner,
                                ALL_PERMISSIONS, 'user', None, self, True,
                                True))
        if self.owner_group_id and not skip_group_perms:
            for user in self.owner_group.users:
                users_perms.append(
                    PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                    self.owner_group, self, True, True))

        return users_perms

    @classmethod
    def by_resource_id(cls, resource_id, db_session=None):
        """ fetch the resouce by id """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.resource_id ==
                                             int(resource_id))
        return query.first()

    @classmethod
    def all(cls, db_session=None):
        """ fetch all permissions"""
        query = get_db_session(db_session).query(cls)
        return query

    @classmethod
    def perm_by_group_and_perm_name(cls, res_id, group_id, perm_name,
                                    db_session=None):
        """ fetch permissions by group and permission name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls._ziggurat_models.GroupResourcePermission)
        query = query.filter(
            cls._ziggurat_models.GroupResourcePermission.group_id == group_id)
        query = query.filter(
            cls._ziggurat_models.GroupResourcePermission.perm_id == perm_name)
        query = query.filter(cls._ziggurat_models.GroupResourcePermission.resource_id == res_id)
        return query.first()

    def groups_for_perm(self, perm_name, group_ids=None,
                        limit_group_permissions=False,
                        db_session=None):
        """ return PermissionTuples for groups that have given
        permission for the resource, perm_name is __any_permission__ then
        users with any permission will be listed
        user_ids - limits the permissions to specific user ids,
        group_ids - limits the permissions to specific group ids,
        """
        db_session = get_db_session(db_session, self)
        group_perms = resource_permissions_for_users(self, [perm_name],
                                                     [self.resource_id],
                                                     group_ids=group_ids,
                                                     limit_group_permissions=limit_group_permissions,
                                                     skip_user_perms=True,
                                                     db_session=db_session)
        if self.owner_group_id:
            for user in self.owner_group.users:
                group_perms.append(
                    PermissionTuple(user, ALL_PERMISSIONS, 'group',
                                    self.owner_group, self, True, True))

        return group_perms


    @classmethod
    def subtree_deeper(cls, object_id, limit_depth=1000000, flat=True,
                       db_session=None):
        """ This returns you subree of ordered objects relative
        to the start object id currently only postgresql
        """
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 as depth, array[ordering] as sorting FROM
                    resources res WHERE res.resource_id = :id
                  UNION ALL
                    SELECT res_u.*, depth+1 as depth,
                    (st.sorting || ARRAY[res_u.ordering] ) as sort
                    FROM resources res_u, subtree st
                    WHERE res_u.parent_id = st.resource_id
            )
            SELECT * FROM subtree WHERE depth<=:depth ORDER BY sorting;
        """
        db_session = get_db_session(db_session)
        q = db_session.query(cls).from_statement(raw_q).params(id=object_id,
                                                               depth=limit_depth)
        return q

    @classmethod
    def path_upper(cls, object_id, limit_depth=1000000, flat=True,
                   db_session=None):
        """ This returns you path to root node starting from object_id
            currently only for postgresql
        """
        raw_q = """
            WITH RECURSIVE subtree AS (
                    SELECT res.*, 1 as depth FROM resources res
                    WHERE res.resource_id = :id
                  UNION ALL
                    SELECT res_u.*, depth+1 as depth
                    FROM resources res_u, subtree st
                    WHERE res_u.resource_id = st.parent_id
            )
            SELECT * FROM subtree WHERE depth<=:depth;
        """
        db_session = get_db_session(db_session)
        q = db_session.query(cls).from_statement(raw_q).params(id=object_id,
                                                               depth=limit_depth)
        return q
