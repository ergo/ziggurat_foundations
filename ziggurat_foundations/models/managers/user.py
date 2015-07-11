import hashlib
import random
import six
import sqlalchemy as sa
import string
from . import ModelManager
from ...utils import get_db_session
from ...permissions import (ANY_PERMISSION,
                            ALL_PERMISSIONS,
                            PermissionTuple,
                            resource_permissions_for_users)


class UserManager(ModelManager):
    @property
    def permissions(self):
        """ returns all non-resource permissions based on what groups user
            belongs and directly set ones for this user"""
        db_session = get_db_session(None, self)
        query = db_session.query(
            self._ziggurat_models.GroupPermission.group_id.label('owner_id'),
            self._ziggurat_models.GroupPermission.perm_name.label('perm_name'),
            sa.literal('group').label('type'))
        query = query.filter(self._ziggurat_models.GroupPermission.group_id ==
                             self._ziggurat_models.UserGroup.group_id)
        query = query.filter(self._ziggurat_models.User.id == self._ziggurat_models.UserGroup.user_id)
        query = query.filter(self._ziggurat_models.User.id == self.id)

        query2 = db_session.query(
            self._ziggurat_models.UserPermission.user_id.label('owner_id'),
            self._ziggurat_models.UserPermission.perm_name.label('perm_name'),
            sa.literal('user').label('type'))
        query2 = query2.filter(self._ziggurat_models.UserPermission.user_id == self.id)
        query = query.union(query2)
        groups_dict = dict([(g.id, g) for g in self.groups])
        return [PermissionTuple(self,
                                row.perm_name,
                                row.type,
                                groups_dict.get(
                                    row.owner_id) if row.type == 'group' else None,
                                None, False, True) for row in query]

    def resources_with_perms(self, perms, resource_ids=None,
                             resource_types=None,
                             db_session=None):
        """ returns all resources that user has perms for,
            note that at least one perm needs to be met,
            resource_ids restricts the search to specific resources"""
        # owned entities have ALL permissions so we return those resources too
        # even without explict perms set
        # TODO: implement admin superrule perm - maybe return all apps
        db_session = get_db_session(db_session, self)
        query = db_session.query(self._ziggurat_models.Resource).distinct()
        group_ids = [gr.id for gr in self.groups]
        # if user has some groups lets try to join based on their permissions
        if group_ids:
            join_conditions = (
                self._ziggurat_models.GroupResourcePermission.group_id.in_(group_ids),
                self._ziggurat_models.Resource.resource_id == self._ziggurat_models.GroupResourcePermission.resource_id,
                self._ziggurat_models.GroupResourcePermission.perm_name.in_(perms),)
            query = query.outerjoin(
                (self._ziggurat_models.GroupResourcePermission,
                 sa.and_(*join_conditions),)
            )
            # ensure outerjoin permissions are correct -
            # dont add empty rows from join
            # conditions are - join ON possible group permissions
            # OR owning group/user
            query = query.filter(sa.or_(
                self._ziggurat_models.Resource.owner_user_id == self.id,
                self._ziggurat_models.Resource.owner_group_id.in_(group_ids),
                self._ziggurat_models.GroupResourcePermission.perm_name != None, ))
        else:
            # filter just by username
            query = query.filter(self._ziggurat_models.Resource.owner_user_id ==
                                 self.id)
        # lets try by custom user permissions for resource
        query2 = db_session.query(self._ziggurat_models.Resource).distinct()
        query2 = query2.filter(self._ziggurat_models.UserResourcePermission.user_id ==
                               self.id)
        query2 = query2.filter(self._ziggurat_models.Resource.resource_id ==
                               self._ziggurat_models.UserResourcePermission.resource_id)
        query2 = query2.filter(
            self._ziggurat_models.UserResourcePermission.perm_name.in_(perms))
        if resource_ids:
            query = query.filter(self._ziggurat_models.Resource.resource_id.in_(resource_ids))
            query2 = query2.filter(self._ziggurat_models.Resource.resource_id.in_(resource_ids))

        if resource_types:
            query = query.filter(
                self._ziggurat_models.Resource.resource_type.in_(resource_types))
            query2 \
                = query2.filter(self._ziggurat_models.Resource.resource_type.in_(resource_types))
        query = query.union(query2)
        query = query.order_by(self._ziggurat_models.Resource.resource_name)
        return query

    def groups_with_resources(self):
        """ Returns a list of groups users belongs to with eager loaded
        resources owned by those groups """

        return self.groups_dynamic.options(
            sa.orm.eagerload(self._ziggurat_models.Group.resources))

    def resources_with_possible_perms(self, resource_ids=None,
                                      resource_types=None,
                                      db_session=None):
        """ returns list of permissions and resources for this user,
            resource_ids restricts the search to specific resources"""
        perms = resource_permissions_for_users(self, ANY_PERMISSION,
                                               resource_ids=resource_ids,
                                               user_ids=[self.id],
                                               db_session=db_session)
        for resource in self.resources:
            perms.append(PermissionTuple(self, ALL_PERMISSIONS, 'user', None,
                                         resource, True, True))
        for group in self.groups_with_resources():
            for resource in group.resources:
                perms.append(
                    PermissionTuple(self, ALL_PERMISSIONS, 'group', group,
                                    resource, True, True))

        return perms


    def gravatar_url(self, default='mm', **kwargs):
        """ returns user gravatar url """
        # construct the url
        hash = hashlib.md5(self.email.encode('utf8').lower()).hexdigest()
        if 'd' not in kwargs:
            kwargs['d'] = default
        params = '&'.join([six.moves.urllib.parse.urlencode({key: value})
                           for key, value in kwargs.items()])
        return "https://secure.gravatar.com/avatar/{}?{}" \
            .format(hash, params)

    def set_password(self, raw_password):
        """ sets new password """
        self.user_password = self.passwordmanager.encode(raw_password)
        self.regenerate_security_code()

    def check_password(self, raw_password):
        """ checks string with users password hash"""
        return self.passwordmanager.check(self.user_password, raw_password,
                                          setter=self.set_password)

    @classmethod
    def generate_random_pass(cls, chars=7):
        """ generates random string of fixed length"""
        return cls.generate_random_string(chars)

    def regenerate_security_code(self):
        """ generates new security code"""
        self.security_code = self.generate_random_string(64)

    @staticmethod
    def generate_random_string(chars=7):
        return u''.join(random.sample(string.ascii_letters * 2 + string.digits,
                                      chars))

    @classmethod
    def by_id(cls, user_id, db_session=None):
        """ fetch user by user name """
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(cls.id == user_id)
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()

    @classmethod
    def by_user_name(cls, user_name, db_session=None):
        """ fetch user by user name """
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(sa.func.lower(cls.user_name) ==
                             (user_name or '').lower())
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()

    @classmethod
    def by_user_name_and_security_code(cls, user_name, security_code,
                                       db_session=None):
        """ fetch user objects by user name and security code"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(sa.func.lower(cls.user_name) ==
                             (user_name or '').lower())
        query = query.filter(cls.security_code == security_code)
        return query.first()

    @classmethod
    def by_user_names(cls, user_names, db_session=None):
        """ fetch user objects by user names """
        user_names = [(name or '').lower() for name in user_names]
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(sa.func.lower(cls.user_name).in_(user_names))
        # q = q.options(sa.orm.eagerload(cls.groups))
        return query

    @classmethod
    def user_names_like(cls, user_name, db_session=None):
        """
        fetch users with similar names

        For now rely on LIKE in db - shouldnt be issue ever
        in future we can plug in fulltext search like solr or whoosh
        """
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(sa.func.lower(cls.user_name).
                             like((user_name or '').lower()))
        query = query.order_by(cls.user_name)
        # q = q.options(sa.orm.eagerload('groups'))
        return query

    @classmethod
    def by_email(cls, email, db_session=None):
        """ fetch user object by email """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(
            sa.func.lower(cls.email) == (email or '').lower())
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()

    @classmethod
    def by_email_and_username(cls, email, user_name, db_session=None):
        """ fetch user object by email and username """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.email == email)
        query = query.filter(sa.func.lower(cls.user_name) ==
                             (user_name or '').lower())
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()

    @classmethod
    def users_for_perms(cls, perm_names, db_session=None):
        """ return users hat have one of given permissions """
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(cls._ziggurat_models.User.id == cls._ziggurat_models.UserGroup.user_id)
        query = query.filter(cls._ziggurat_models.UserGroup.group_id ==
                             cls._ziggurat_models.GroupPermission.group_id)
        query = query.filter(
            cls._ziggurat_models.GroupPermission.perm_name.in_(perm_names))

        query2 = db_session.query(cls)
        query2 = query2.filter(cls._ziggurat_models.User.id ==
                               cls._ziggurat_models.UserPermission.user_id)
        query2 = query2.filter(cls._ziggurat_models.UserPermission.perm_name.in_(perm_names))
        users = query.union(query2).order_by(cls.id)
        return users