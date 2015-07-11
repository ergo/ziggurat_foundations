import sqlalchemy as sa
from datetime import datetime, timedelta
from sqlalchemy.ext.declarative import declared_attr
from ziggurat_foundations.permissions import ANY_PERMISSION, ALL_PERMISSIONS, Allow, Deny, PermissionTuple
from ziggurat_foundations.utils import get_db_session

# should hold global scoped session
DBSession = None


def groupfinder(userid, request):
    if userid and hasattr(request, 'user') and request.user:
        groups = ['group:%s' % g.group_name for g in request.user.groups]
        return groups
    return []


class BaseModel(object):
    """ Basic class that all other classes inherit from that supplies some
    basic methods useful for interaction with packages like:
    deform, colander or wtforms """

    @classmethod
    def _get_keys(cls):
        """ returns column names for this model """
        return sa.orm.class_mapper(cls).c.keys()

    def get_dict(self, exclude_keys=None, include_keys=None):
        """ return dictionary of keys and values corresponding to this model's
        data
        if include_keys is null the function will return all keys

        ::arg include_keys (optional) is a list of columns from model that
        should be returned by this function
        ::arg exclude_keys (optional) is a list of columns from model that
        should not be returned by this function
        """
        d = {}
        exclude_keys_list = exclude_keys or []
        include_keys_list = include_keys or []
        for k in self._get_keys():
            if k not in exclude_keys_list and \
                    (k in include_keys_list or not include_keys):
                d[k] = getattr(self, k)
        return d

    def get_appstruct(self):
        """ return list of tuples keys and values corresponding to this model's
        data """
        l = []
        for k in self._get_keys():
            l.append((k, getattr(self, k),))
        return l

    def populate_obj(self, appstruct):
        """ updates instance properties with dictionary values *for keys that
        exist* for this model """
        for k in self._get_keys():
            if k in appstruct:
                setattr(self, k, appstruct[k])

    def get_db_session(self, session=None):
        """ Attempts to return session via get_db_session utility function
        :meth:`~ziggurat_foundations.models.get_db_session`"""
        return get_db_session(session, self)

    def persist(self, flush=False, db_session=None):
        """
        Adds object to session, if the object was freshly created this will
        persist the object in the storage on commit

        :param flush: boolean - if true then the session will be flushed
        instantly
        :param db_session:
        :return:
        """
        db_session = get_db_session(db_session)
        db_session.add(self)
        if flush:
            db_session.flush()

    def delete(self, db_session=None):
        """ Deletes the object via session, this will permanently delete the
        object from storage on commit """
        db_session = get_db_session(db_session, self)
        db_session.delete(self)

    @classmethod
    def base_query(cls, db_session=None):
        """
        Returns a base query object one can use to search on simple properties
        :param db_session:
        :return:
        """
        return get_db_session(db_session).query(cls)


from ziggurat_foundations.managers import (
    GroupManager,
    GroupPermissionManager,
    ExternalIdentityManager,
    UserResourcePermissionManager,
    UserPermissionManager,
    UserManager,
    ResourceManager
)


class UserMixin(UserManager, BaseModel):
    """ Base mixin for user object representation.
        It supplies all the basic functionality from password hash generation
        and matching to utility methods used for querying database for users
        and their permissions or resources they have access to. It is meant
        to be extended with other application specific properties"""

    __mapper_args__ = {}
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'
    }

    @declared_attr
    def __tablename__(self):
        return 'users'

    @declared_attr
    def id(self):
        """ Unique identifier of user object"""
        return sa.Column(sa.Integer, primary_key=True, autoincrement=True)

    @declared_attr
    def user_name(self):
        """ Unique user name user object"""
        return sa.Column(sa.Unicode(30), unique=True)

    @declared_attr
    def user_password(self):
        """ Password hash for user object """
        return sa.Column(sa.String(256))

    @declared_attr
    def email(self):
        """ Email for user object """
        return sa.Column(sa.Unicode(100), nullable=False, unique=True)

    @declared_attr
    def status(self):
        """ Status of user object """
        return sa.Column(sa.SmallInteger(), nullable=False, default=1)

    @declared_attr
    def security_code(self):
        """ Security code user object (can be used for password reset etc. """
        return sa.Column(sa.String(256), default='default')

    @declared_attr
    def last_login_date(self):
        """ Date of user's last login """
        return sa.Column(sa.TIMESTAMP(timezone=False),
                         default=lambda x: datetime.utcnow(),
                         server_default=sa.func.now())

    @declared_attr
    def registered_date(self):
        """ Date of user's registration """
        return sa.Column(sa.TIMESTAMP(timezone=False),
                         default=lambda x: datetime.utcnow(),
                         server_default=sa.func.now())

    @declared_attr
    def security_code_date(self):
        """ Date of user's security code update """
        return sa.Column(sa.TIMESTAMP(timezone=False),
                         default=datetime(2000, 1, 1),
                         server_default='2000-01-01 01:01')

    def __repr__(self):
        return '<User: %s>' % self.user_name

    @declared_attr
    def groups_dynamic(self):
        """ returns dynamic relationship for groups - allowing for
        filtering of data """
        return sa.orm.relationship('Group', secondary='users_groups',
                                   lazy='dynamic',
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def user_permissions(self):
        """
        returns all direct non-resource permissions for this user,
        allows to assign new permissions to user::

            user.user_permissions.append(resource)
        """
        return sa.orm.relationship('UserPermission',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def resource_permissions(self):
        """ returns all direct resource permissions for this user """
        return sa.orm.relationship('UserResourcePermission',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True
        )

    @declared_attr
    def resources(cls):
        """ Returns all resources directly owned by user, can be used to assign
        ownership of new resources::

            user.resources.append(resource) """
        return sa.orm.relationship('Resource',
                                   cascade="all",
                                   passive_deletes=True,
                                   passive_updates=True,
                                   backref='owner',
                                   lazy='dynamic')

    @declared_attr
    def external_identities(self):
        """ dynamic relation for external identities for this user -
        allowing for filtering of data """
        return sa.orm.relationship('ExternalIdentity',
                                   lazy='dynamic',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True,
                                   backref='owner')


class ExternalIdentityMixin(ExternalIdentityManager, BaseModel):
    @declared_attr
    def __tablename__(self):
        return 'external_identities'

    @declared_attr
    def external_id(self):
        return sa.Column(sa.Unicode(255), default=u'', primary_key=True)

    @declared_attr
    def external_user_name(self):
        return sa.Column(sa.Unicode(255), default=u'')

    @declared_attr
    def local_user_name(self):
        return sa.Column(sa.Unicode(50), sa.ForeignKey('users.user_name',
                                                       onupdate='CASCADE',
                                                       ondelete='CASCADE'),
                         primary_key=True)

    @declared_attr
    def provider_name(self):
        return sa.Column(sa.Unicode(50), default=u'', primary_key=True)

    @declared_attr
    def access_token(self):
        return sa.Column(sa.String(255), default=u'')

    @declared_attr
    def alt_token(self):
        return sa.Column(sa.String(255), default=u'')

    @declared_attr
    def token_secret(self):
        return sa.Column(sa.String(255), default=u'')


class GroupMixin(GroupManager, BaseModel):
    """ base mixin for group object"""

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups'

    # lists app wide permissions we might want to assign to groups
    __possible_permissions__ = ()

    @declared_attr
    def id(self):
        return sa.Column(sa.Integer(), primary_key=True, )

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(128), nullable=False)

    @declared_attr
    def description(self):
        return sa.Column(sa.Text())

    @declared_attr
    def member_count(self):
        return sa.Column(sa.Integer, nullable=False, default=0)

    @declared_attr
    def users(self):
        """ relationship for users belonging to this group"""
        return sa.orm.relationship('User',
                                   secondary='users_groups',
                                   order_by='User.user_name',
                                   passive_deletes=True,
                                   passive_updates=True,
                                   backref='groups')

    # dynamic property - useful
    @declared_attr
    def users_dynamic(self):
        """ dynamic relationship for users belonging to this group
            one can use filter """
        return sa.orm.relationship('User',
                                   secondary='users_groups',
                                   order_by='User.user_name',
                                   lazy="dynamic")

    @declared_attr
    def permissions(self):
        """ non-resource permissions assigned to this group"""
        return sa.orm.relationship('GroupPermission',
                                   backref='groups',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def resource_permissions(self):
        """ permissions to specific resources this group has"""
        return sa.orm.relationship('GroupResourcePermission',
                                   backref='groups',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def resources(cls):
        """ Returns all resources directly owned by group, can be used to assign
        ownership of new resources::

            user.resources.append(resource) """
        return sa.orm.relationship('Resource',
                                   cascade="all",
                                   passive_deletes=True,
                                   passive_updates=True,
                                   backref='owner_group')

    @declared_attr
    def resources_dynamic(cls):
        """ Returns all resources directly owned by group, can be used to assign
        ownership of new resources::

            user.resources.append(resource) """
        return sa.orm.relationship('Resource',
                                   cascade="all",
                                   passive_deletes=True,
                                   passive_updates=True,
                                   lazy='dynamic')

    def __repr__(self):
        return '<Group: %s, %s>' % (self.group_name, self.id)


class GroupPermissionMixin(GroupPermissionManager, BaseModel):
    """ group permission mixin """

    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups_permissions'

    @declared_attr
    def group_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('groups.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(30), primary_key=True)

    def __repr__(self):
        return '<GroupPermission: %s>' % self.perm_name


class UserPermissionMixin(UserPermissionManager, BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_permissions'

    @declared_attr
    def user_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(30), primary_key=True)

    def __repr__(self):
        return '<UserPermission: %s>' % self.perm_name


class UserGroupMixin(BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_groups'

    @declared_attr
    def group_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('groups.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def user_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    def __repr__(self):
        return '<UserGroup: g:%s, u:%s>' % (self.group_id, self.user_id,)


class GroupResourcePermissionMixin(BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups_resources_permissions'

    @declared_attr
    def group_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('groups.id',
                                                   onupdate='CASCADE',
                                                   ondelete='CASCADE'),
                         primary_key=True)

    @declared_attr
    def resource_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('resources.resource_id',
                                       onupdate='CASCADE',
                                       ondelete='CASCADE'),
                         primary_key=True,
                         autoincrement=False)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(50), primary_key=True)

    def __repr__(self):
        return '<GroupResourcePermission: g:%s, %s, r:%s>' % (self.group_id,
                                                              self.perm_name,
                                                              self.resource_id,)


class UserResourcePermissionMixin(UserResourcePermissionManager, BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_resources_permissions'

    @declared_attr
    def user_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('users.id',
                                                   onupdate='CASCADE',
                                                   ondelete='CASCADE'),
                         primary_key=True)

    @declared_attr
    def resource_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('resources.resource_id',
                                       onupdate='CASCADE',
                                       ondelete='CASCADE'),
                         primary_key=True,
                         autoincrement=False)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(50), primary_key=True)

    def __repr__(self):
        return '<userResourcePermission: %s, %s, %s>' % (self.user_id,
                                                         self.perm_name,
                                                         self.resource_id,)


class ResourceMixin(ResourceManager, BaseModel):
    __possible_permissions__ = ()

    @declared_attr
    def __tablename__(self):
        return 'resources'

    @declared_attr
    def resource_id(self):
        return sa.Column(sa.Integer(), primary_key=True, nullable=False,
                         autoincrement=True)

    @declared_attr
    def parent_id(self):
        return sa.Column(sa.Integer(),
                         sa.ForeignKey('resources.resource_id',
                                       onupdate='CASCADE', ondelete='SET NULL'))

    @declared_attr
    def ordering(self):
        return sa.Column(sa.Integer(), default=0, nullable=False)

    @declared_attr
    def resource_name(self):
        return sa.Column(sa.Unicode(100), nullable=False)

    @declared_attr
    def resource_type(self):
        return sa.Column(sa.Unicode(30), nullable=False)

    @declared_attr
    def owner_group_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('groups.id', onupdate='CASCADE',
                                       ondelete='SET NULL'), index=True)

    @declared_attr
    def owner_user_id(self):
        return sa.Column(sa.Integer,
                         sa.ForeignKey('users.id', onupdate='CASCADE',
                                       ondelete='SET NULL'), index=True)

    @declared_attr
    def group_permissions(self):
        """ returns all group permissions for this resource"""
        return sa.orm.relationship('GroupResourcePermission',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def user_permissions(self):
        """ returns all user permissions for this resource"""
        return sa.orm.relationship('UserResourcePermission',
                                   cascade="all, delete-orphan",
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def groups(self):
        """ returns all groups that have permissions for this resource"""
        return sa.orm.relationship('Group',
                                   secondary='groups_resources_permissions',
                                   passive_deletes=True,
                                   passive_updates=True)

    @declared_attr
    def users(self):
        """ returns all users that have permissions for this resource"""
        return sa.orm.relationship('User',
                                   secondary='users_resources_permissions',
                                   passive_deletes=True,
                                   passive_updates=True)

    __mapper_args__ = {'polymorphic_on': resource_type}
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    def __repr__(self):
        return '<Resource: %s, %s, id: %s>' % (self.resource_type,
                                               self.resource_name,
                                               self.resource_id,)

    @property
    def __acl__(self):
        raise Exception("The model should have implemented __acl__")
