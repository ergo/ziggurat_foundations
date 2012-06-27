import sqlalchemy as sa
import hashlib
import urllib
import random
import string
import webhelpers.paginate

from sqlalchemy.ext.declarative import declared_attr

try:
    from pyramid.security import Allow, ALL_PERMISSIONS
except ImportError as e:
    Allow = 'Allow'
    # borrowed directly from pyramid - to avoid dependancy on pyramid itself
    # source https://github.com/Pylons/pyramid/blob/master/pyramid/security.py

    class AllPermissionsList(object):
        """ Stand in 'permission list' to represent all permissions """

        def __iter__(self):
            return ()

        def __contains__(self, other):
            return True

        def __eq__(self, other):
            return isinstance(other, self.__class__)

    ALL_PERMISSIONS = AllPermissionsList()

__version__ = '0.2'
DBSession = None


def get_db_session(session=None, obj=None):
    """ utility function that attempts to return sqlalchemy session that could 
    have been created/passed in one of few ways:

    * It first tries to read session attached to instance 
      if object argument was passed

    * then it tries to return  session passed as argument

    * finally tries to read pylons-like object called DBSession

    * if this fails exception is thrown """
    # try to read the session from instance
    if obj:
        return sa.orm.session.object_session(obj)
    #try passed session
    elif session:
        return session
    #try global pylons-like session then
    elif DBSession:
        return DBSession
    raise Exception('No Session found')


def groupfinder(userid, request):
    if userid and hasattr(request, 'user') and request.user:
        groups = ['group:%s' % g.group_name.lower() for g in request.user.groups]
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

    def get_dict(self):
        """ return dictionary of keys and values corresponding to this model's
        data """
        d = {}
        for k in self._get_keys():
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


class UserMixin(BaseModel):
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
        return sa.Column(sa.SmallInteger(), nullable=False)

    @declared_attr
    def security_code(self):
        """ Security code user object (can be used for password reset etc. """
        return sa.Column(sa.String(256), default='default')

    @declared_attr
    def last_login_date(self):
        """ Date of user's last login """
        return sa.Column(sa.TIMESTAMP(timezone=False),
                                default=sa.sql.func.now(),
                                server_default=sa.func.now()
                                )

    @declared_attr
    def registered_date(self):
        """ Date of user's registration """
        return sa.Column(sa.TIMESTAMP(timezone=False),
                                default=sa.sql.func.now(),
                                server_default=sa.func.now()
                                )

    def __repr__(self):
        return '<User: %s>' % self.user_name

    @declared_attr
    def groups_dynamic(self):
        """ returns dynamic relationship for groups - allowing for 
        filtering of data """
        return sa.orm.relationship('Group', secondary='users_groups',
                        lazy='dynamic',
                        passive_deletes=True,
                        passive_updates=True
                        )

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
                        passive_updates=True
                        )

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
                        backref='owner'
                        )

    @declared_attr
    def external_identities(self):
        """ dynamic relation for external identities for this user - 
        allowing for filtering of data """
        return sa.orm.relationship('ExternalIdentity',
                        lazy='dynamic',
                        cascade="all, delete-orphan",
                        passive_deletes=True,
                        passive_updates=True,
                        backref='owner'
                        )

    @property
    def permissions(self):
        """ returns all non-resource permissions based on what groups user
            belongs and directly set ones for this user"""
        db_session = get_db_session(None, self)
        query = db_session.query((u'group:' + \
                        self.GroupPermission.group_name).label('owner_name'),
                             self.GroupPermission.perm_name.label('perm_name'))
        query = query.filter(self.GroupPermission.group_name == \
                             self.UserGroup.group_name)
        query = query.filter(self.User.user_name == self.UserGroup.user_name)
        query = query.filter(self.User.user_name == self.user_name)

        query2 = db_session.query(
                            self.UserPermission.user_name.label('owner_name'),
                            self.UserPermission.perm_name.label('perm_name'))
        query2 = query2.filter(self.UserPermission.user_name == self.user_name)
        query = query.union(query2)
        return [(row.owner_name, row.perm_name) for row in query]

    def resources_with_perms(self, perms, resource_ids=None,
                             db_session=None):
        """ returns all resources that user has perms for,
            note that at least one perm needs to be met,
            resource_ids restricts the search to specific resources"""
        # owned entities have ALL permissions so we return those resources too
        # even without explict perms set
        # TODO: implement admin superrule perm - maybe return all apps
        db_session = get_db_session(db_session, self)
        query = db_session.query(self.Resource).distinct()
        group_names = [gr.group_name for gr in self.groups]
        #if user has some groups lets try to join based on their permissions
        if group_names:
            join_conditions = (
        self.GroupResourcePermission.group_name.in_(group_names),
        self.Resource.resource_id == self.GroupResourcePermission.resource_id,
        self.GroupResourcePermission.perm_name.in_(perms),)
            query = query.outerjoin(
                            (self.GroupResourcePermission,
                             sa.and_(*join_conditions),)
                            )
            # ensure outerjoin permissions are correct - 
            # dont add empty rows from join
            # conditions are - join ON possible group permissions 
            # OR owning group/user
            query = query.filter(sa.or_(
                            self.Resource.owner_user_name == self.user_name,
                            self.Resource.owner_group_name.in_(group_names),
                            self.GroupResourcePermission.perm_name != None,))
        else:
            #filter just by username
            query = query.filter(self.Resource.owner_user_name == \
                                 self.user_name)
        # lets try by custom user permissions for resource
        query2 = db_session.query(self.Resource).distinct()
        query2 = query2.filter(self.UserResourcePermission.user_name == \
                               self.user_name)
        query2 = query2.filter(self.Resource.resource_id == \
                               self.UserResourcePermission.resource_id)
        query2 = query2.filter(
                            self.UserResourcePermission.perm_name.in_(perms))
        if resource_ids:
            query = query.filter(self.Resource.resource_id.in_(resource_ids))
            query2 = query2.filter(self.Resource.resource_id.in_(resource_ids))
        query = query.union(query2)
        query = query.order_by(self.Resource.resource_name)
        return query

    def gravatar_url(self, default='mm'):
        """ returns user gravatar url """
        # construct the url
        hash = hashlib.md5(self.email.encode('utf8').lower()).hexdigest()
        gravatar_url = "https://secure.gravatar.com/avatar/%s?%s" % (
                                    hash, urllib.urlencode({'d': default}))
        return gravatar_url

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
        self.security_code = self.generate_random_string(32)

    @staticmethod
    def generate_random_string(chars=7):
        return u''.join(random.sample(string.ascii_letters + string.digits,
                                      chars))

    @classmethod
    def by_user_name(cls, user_name, db_session=None):
        """ fetch user by user name """
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(sa.func.lower(cls.user_name) == \
                             (user_name or '').lower())
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()

    @classmethod
    def by_user_name_and_security_code(cls, user_name, security_code,
                                       db_session=None):
        """ fetch user objects by user name and security code"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(sa.func.lower(cls.user_name) == \
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
        #q = q.options(sa.orm.eagerload(cls.groups))
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
        query = query.filter(sa.func.lower(cls.user_name).\
                             like((user_name or '').lower()))
        query = query.order_by(cls.user_name)
        #q = q.options(sa.orm.eagerload('groups'))
        return query

    @classmethod
    def by_email(cls, email, db_session=None):
        """ fetch user objects by email """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.email == email)
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()

    @classmethod
    def by_email_and_username(cls, email, user_name, db_session=None):
        """ fetch user objects by email and username """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.email == email)
        query = query.filter(sa.func.lower(cls.user_name) == \
                             (user_name or '').lower())
        query = query.options(sa.orm.eagerload('groups'))
        return query.first()


class ExternalIdentityMixin(BaseModel):

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
                         onupdate='CASCADE', ondelete='CASCADE'),
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

    @classmethod
    def by_external_id_and_provider(cls, external_id, provider_name,
                                 db_session=None):
        db_session = get_db_session(db_session)
        query = db_session.query(cls)
        query = query.filter(cls.external_id == external_id)
        query = query.filter(cls.provider_name == provider_name)
        return query.first()

    @classmethod
    def user_by_external_id_and_provider(cls, external_id, provider_name,
                                 db_session=None):
        db_session = get_db_session(db_session)
        query = db_session.query(cls.User)
        query = query.filter(cls.external_id == external_id)
        query = query.filter(cls.User.user_name == cls.local_user_name)
        query = query.filter(cls.provider_name == provider_name)
        return query.first()


class GroupMixin(BaseModel):
    """ base mixin for group object"""

    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups'

    # lists app wide permissions we might want to assign to groups
    __possible_permissions__ = ('root_administration',
                                'administration',
                                'backend_admin_panel',
                                'manage_apps',)

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(128), primary_key=True,)

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
                        backref='groups'
                        )

    # dynamic property - useful
    @declared_attr
    def users_dynamic(self):
        """ dynamiec relationship for users belonging to this group
            one can use filter """
        return sa.orm.relationship('User',
                        secondary='users_groups',
                        order_by='User.user_name',
                        lazy="dynamic"
                        )

    @declared_attr
    def permissions(self):
        """ non-resource permissions assigned to this group"""
        return sa.orm.relationship('GroupPermission',
                        backref='groups',
                        cascade="all, delete-orphan",
                        passive_deletes=True,
                        passive_updates=True
                        )

    @declared_attr
    def resource_permissions(self):
        """ permissions to specific resources this group has"""
        return sa.orm.relationship('GroupResourcePermission',
                        backref='groups',
                        cascade="all, delete-orphan",
                        passive_deletes=True,
                        passive_updates=True
                        )

    def __repr__(self):
        return '<Group: %s>' % self.group_name

    @classmethod
    def all(cls, db_session=None):
        """ return all groups"""
        query = get_db_session(db_session).query(cls)
        return query

    @classmethod
    def by_group_name(cls, group_name, db_session=None):
        """ fetch group by name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.group_name == group_name)
        return query.first()

    @sa.orm.validates('permissions')
    def validate_permission(self, key, permission):
        """ validates if group can get assigned with permission"""
        assert permission.perm_name in self.__possible_permissions__
        return permission

    def get_user_paginator(self, page=1, item_count=None, items_per_page=50,
                           user_names=None, GET_params={}):
        """ returns paginator over users belonging to the group"""
        GET_params.pop('page', None)
        query = self.users_dynamic
        if user_names:
            query = query.filter(self.UserGroup.user_name.in_(user_names))
        return webhelpers.paginate.Page(query, page=page,
                                     item_count=item_count,
                                     items_per_page=items_per_page,
                                     **GET_params
                                     )


class GroupPermissionMixin(BaseModel):
    """ group permission mixin """

    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups_permissions'

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(50),
                        sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(30), primary_key=True)

    def __repr__(self):
        return '<GroupPermission: %s>' % self.perm_name

    @classmethod
    def by_group_and_perm(cls, group_name, perm_name, db_session=None):
        """" return all instances by group and permission names """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.group_name == group_name)
        query = query.filter(cls.perm_name == perm_name)
        return query.first()


class UserPermissionMixin(BaseModel):

    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_permissions'

    @declared_attr
    def user_name(self):
        return sa.Column(sa.Unicode(50),
                         sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def perm_name(self):
        return sa.Column(sa.Unicode(30), primary_key=True)

    def __repr__(self):
        return '<UserPermission: %s>' % self.perm_name

    @classmethod
    def by_user_and_perm(cls, user_name, perm_name, db_session=None):
        """ return all instances by user and permission name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.user_name == user_name)
        query = query.filter(cls.perm_name == perm_name)
        return query.first()


class UserGroupMixin(BaseModel):

    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_groups'

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(50),
                         sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def user_name(self):
        return sa.Column(sa.Unicode(30),
                        sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True)

    def __repr__(self):
        return '<UserGroup: %s, %s>' % (self.group_name, self.user_name,)


class GroupResourcePermissionMixin(BaseModel):

    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'groups_resources_permissions'

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(50), sa.ForeignKey('groups.group_name',
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
        return '<GroupResourcePermission: %s, %s, %s>' % (self.group_name,
                                                      self.perm_name,
                                                      self.resource_id,)


class UserResourcePermissionMixin(BaseModel):

    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    @declared_attr
    def __tablename__(self):
        return 'users_resources_permissions'

    @declared_attr
    def user_name(self):
        return sa.Column(sa.Unicode(50), sa.ForeignKey('users.user_name',
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
        return '<userResourcePermission: %s, %s, %s>' % (self.user_name,
                                                      self.perm_name,
                                                      self.resource_id,)

    @classmethod
    def by_resource_user_and_perm(cls, user_name, perm_name, resource_id,
                                  db_session=None):
        """ return all instances by user name, perm name and resource id """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.user_name == user_name)
        query = query.filter(cls.resource_id == resource_id)
        query = query.filter(cls.perm_name == perm_name)
        return query.first()

#    @classmethod
#    def allowed_permissions(cls, key):
#        """ ensures we can only use permission that can be assigned 
#            to this resource type"""
#        if key in cls.__possible_permissions__:
#            return key
#        raise KeyError


class ResourceMixin(BaseModel):

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
    def owner_group_name(self):
        return sa.Column(sa.Unicode(50),
                       sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                     ondelete='SET NULL'), index=True)

    @declared_attr
    def owner_user_name(self):
        return sa.Column(sa.Unicode(30),
                       sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                     ondelete='SET NULL'), index=True)

    @declared_attr
    def group_permissions(self):
        """ returns all group permissions for this resource"""
        return sa.orm.relationship('GroupResourcePermission',
                                  cascade="all, delete-orphan",
                                  passive_deletes=True,
                                  passive_updates=True
                                  )

    @declared_attr
    def user_permissions(self):
        """ returns all user permissions for this resource"""
        return sa.orm.relationship('UserResourcePermission',
                                  cascade="all, delete-orphan",
                                  passive_deletes=True,
                                  passive_updates=True
                                  )

    @declared_attr
    def groups(self):
        """ returns all groups that have permissions for this resource"""
        return sa.orm.relationship('Group',
                                 secondary='groups_resources_permissions',
                                 passive_deletes=True,
                                 passive_updates=True
                                  )

    @declared_attr
    def users(self):
        """ returns all users that have permissions for this resource"""
        return sa.orm.relationship('User',
                                 secondary='users_resources_permissions',
                                 passive_deletes=True,
                                 passive_updates=True
                                  )

    __mapper_args__ = {'polymorphic_on': resource_type}
    __table_args__ = {'mysql_engine':'InnoDB', 'mysql_charset':'utf8'}

    def __repr__(self):
        return '<Resource: %s, %s, id: %s>' % (self.resource_type,
                                               self.resource_name,
                                               self.resource_id,
                                               )

    @property
    def __acl__(self):
        acls = [(Allow, 'group:administrators', ALL_PERMISSIONS,), ]

        if self.owner_user_name:
            acls.extend([(Allow, self.owner_user_name, ALL_PERMISSIONS,), ])

        if self.owner_group_name:
            acls.extend([(Allow, "group:%s" % self.owner_group_name,
                          ALL_PERMISSIONS,), ])
        return acls

    def perms_for_user(self, user, db_session=None):
        """ returns all permissions that given user has for this resource
            from groups and directly set ones too"""
        db_session = get_db_session(db_session, self)
        query = db_session.query(
                        u'group:' + self.GroupResourcePermission.group_name,
                        self.GroupResourcePermission.perm_name)
        query = query.filter(self.GroupResourcePermission.group_name.in_(
                                        [gr.group_name for gr in user.groups]
                                        )
                     )
        query = query.filter(self.GroupResourcePermission.resource_id == \
                             self.resource_id)

        query2 = db_session.query(self.UserResourcePermission.user_name,
                              self.UserResourcePermission.perm_name)
        query2 = query2.filter(self.UserResourcePermission.user_name == \
                               user.user_name)
        query2 = query2.filter(self.UserResourcePermission.resource_id == \
                               self.resource_id)
        query = query.union(query2)
        perms = [(row[0], row.perm_name,) for row in query]
        #include all perms if user is the owner of this resource
        if self.owner_user_name == user.user_name:
            perms.append((self.owner_user_name, ALL_PERMISSIONS,))
        return perms

    def direct_perms_for_user(self, user, db_session=None):
        """ returns permissions that given user has for this resource
            without ones inherited from groups that user belongs to"""
        db_session = get_db_session(db_session, self)
        query = db_session.query(self.UserResourcePermission.user_name,
                             self.UserResourcePermission.perm_name)
        query = query.filter(self.UserResourcePermission.user_name == \
                             user.user_name)
        query = query.filter(self.UserResourcePermission.resource_id == \
                             self.resource_id)
        perms = [(row[0], row.perm_name,) for row in query]
        #include all perms if user is the owner of this resource
        if self.owner_user_name == user.user_name:
            perms.append((self.owner_user_name, ALL_PERMISSIONS,))
        return perms

    def group_perms_for_user(self, user, db_session=None):
        """ returns permissions that given user has for this resource
            that are inherited from groups """
        db_session = get_db_session(db_session, self)
        query = db_session.query(
                        u'group:' + self.GroupResourcePermission.group_name,
                        self.GroupResourcePermission.perm_name)
        query = query.filter(self.GroupResourcePermission.group_name.in_(
                                    [gr.group_name for gr in user.groups]
                                    )
                     )
        query = query.filter(self.GroupResourcePermission.resource_id == \
                             self.resource_id)
        perms = [(row[0], row.perm_name,) for row in query]
#        if self.owner_group_name:
#            perms.append(('group:' + self.owner_group_name, ALL_PERMISSIONS,))
        return perms

    def users_for_perm(self, perm_name, db_session=None):
        """ return tuple (user,perm_name) that have given 
        permission for the resource """
        db_session = get_db_session(db_session, self)
        query = db_session.query(self.User,
                                 self.GroupResourcePermission.perm_name)
        query = query.filter(self.User.user_name == self.UserGroup.user_name)
        query = query.filter(self.UserGroup.group_name == \
                             self.GroupResourcePermission.group_name)
        if perm_name != '__any_permission__':
            query = query.filter(self.GroupResourcePermission.perm_name == \
                                 perm_name)
        query = query.filter(self.GroupResourcePermission.resource_id == \
                             self.resource_id)
        query2 = db_session.query(self.User,
                                  self.UserResourcePermission.perm_name)
        query2 = query2.filter(self.User.user_name == \
                               self.UserResourcePermission.user_name)
        if perm_name != '__any_permission__':
            query2 = query2.filter(self.UserResourcePermission.perm_name == \
                                   perm_name)
        query2 = query2.filter(self.UserResourcePermission.resource_id == \
                               self.resource_id)
        query = query.union(query2)
        users = [(row.User, row.perm_name,) for row in query]
        if self.owner_user_name:
            users.append((self.User.by_user_name(self.owner_user_name),
                          ALL_PERMISSIONS,))
        return users

    @classmethod
    def by_resource_id(cls, resource_id, db_session=None):
        """ fetch the resouce by id """
        db_session = get_db_session(db_session)
        query = db_session.query(cls).filter(cls.resource_id == \
                                             int(resource_id))
        return query.first()

    @classmethod
    def all(cls, db_session=None):
        """ fetch all permissions"""
        query = get_db_session(db_session).query(cls)
        return query

    @classmethod
    def perm_by_group_and_perm_name(cls, res_id, group_name, perm_name,
                                    db_session=None):
        """ fetch permissions by group and permission name"""
        db_session = get_db_session(db_session)
        query = db_session.query(cls.GroupResourcePermission)
        query = query.filter(
                        cls.GroupResourcePermission.group_name == group_name)
        query = query.filter(
                        cls.GroupResourcePermission.perm_name == perm_name)
        query = query.filter(cls.GroupResourcePermission.resource_id == res_id)
        return query.first()

    @sa.orm.validates('user_permissions', 'group_permissions')
    def validate_permission(self, key, permission):
        """ validate if resouce can have specific permission """
        assert permission.perm_name in self.__possible_permissions__
        return permission

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
