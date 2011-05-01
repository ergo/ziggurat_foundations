import sqlalchemy as sa
import sqlalchemy.orm as orm
import hashlib
import urllib
import random

from cryptacular.bcrypt import BCRYPTPasswordManager
from cryptacular.core import DelegatingPasswordManager
from pyramid_reactor.utils import PlaceholderPasswordChecker
from sqlalchemy.ext.declarative import declared_attr
from pyramid.security import Allow, Everyone, Authenticated, ALL_PERMISSIONS


DBSession = None



class BaseModel(object):
    
    def db_session(self):
        return 
    
    @classmethod
    def _get_keys(cls):
        """ return column names for this model """ 
        return sa.orm.class_mapper(cls).c.keys()
    
    def get_dict(self):
        """ return dict with keys and values corresponding to this model data """
        d = {}
        for k in self._get_keys():
            d[k] = getattr(self, k)
        return d
    
    def get_appstruct(self):
        """ return dict with keys and values corresponding to this model data """
        l = []
        for k in self._get_keys():
            l.append((k, getattr(self, k),))
        return l
    
    def populate_obj(self, appstruct):
        """ populate model with data from appstruct """
        for k in self._get_keys():
            if k in appstruct:
                setattr(self, k, appstruct[k])
    
    @classmethod            
    def get_db_session(cls, session=None):
        #try passed session first
        if session:
            return session
        #try global pylons-like session then
        elif DBSession:
            return DBSession
        # finally try to read the session from instance - this can fail ;-)
        else:
            return sa.orm.session.object_session(cls)
            
                
class UserMapperExtension(sa.orm.interfaces.MapperExtension):
    
    def after_update(self, mapper, connection, instance):
        instance.by_user_name(instance.user_name, invalidate=True)
        
    def after_delete(self, mapper, connection, instance):
        instance.by_user_name(instance.user_name, invalidate=True)
                
class UserMixin(BaseModel):
    __mapper_args__ = {'extension': UserMapperExtension()}
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    
    @declared_attr
    def id(cls):
        return sa.Column(sa.Integer, primary_key=True)
    
    @declared_attr
    def user_name(cls):
        return sa.Column(sa.Unicode(30), unique=True)
    
    @declared_attr
    def user_password(cls):
        return sa.Column(sa.String(40))
    
    @declared_attr
    def email(cls):
        return sa.Column(sa.Unicode(100), nullable=False, unique=True)
    
    @declared_attr
    def status(cls):
        return sa.Column(sa.SmallInteger(), nullable=False)
    
    @declared_attr
    def security_code(cls):
        return sa.Column(sa.String(40), default='default')
    
    @declared_attr
    def last_login_date(cls):
        return sa.Column(sa.TIMESTAMP(timezone=True),
                                default=sa.sql.func.now(),
                                server_default=sa.func.now()
                                )
    
    passwordmanager = DelegatingPasswordManager(
            preferred=BCRYPTPasswordManager(),
            fallbacks=(PlaceholderPasswordChecker(),)
            )
    
    def __repr__(self):
        return '<User: %s>' % self.user_name
    
    @declared_attr
    def groups_dynamic(cls):
        return sa.orm.relationship('Group', secondary='users_groups',
                        lazy='dynamic',
                        passive_deletes=True,
                        passive_updates=True
                        )
    
    @declared_attr
    def user_permissions(cls):
        return sa.orm.relationship('UserPermission',
                        cascade="all, delete-orphan",
                        passive_deletes=True,
                        passive_updates=True
                        )

    @declared_attr
    def resource_permissions(cls):
        return sa.orm.relationship('UserResourcePermission',
                        cascade="all, delete-orphan",
                        passive_deletes=True,
                        passive_updates=True
                        )
    
    @declared_attr
    def resources(cls):
        return sa.orm.relationship('Resource',
                        cascade="all",
                        passive_deletes=True,
                        passive_updates=True,
                        backref='owner'
                        )
    
    @property
    def permissions(self, db_session=None):
        db_session = self.get_db_session(db_session)
        q = db_session.query(GroupPermission.perm_name.label('perm_name'))
        q = q.filter(GroupPermission.group_name == UserGroup.group_name)
        q = q.filter(User.user_name == UserGroup.user_name)
        q = q.filter(User.user_name == self.user_name)
        
        q2 = db_session.query(UserPermission.perm_name.label('perm_name'))
        q2 = q2.filter(User.user_name == self.user_name)
        q = q.union(q2)
        return [row.perm_name for row in q]
        
        
    
    def resources_with_perms(self, perms, resource_ids=None,
                             cache='default',
                             invalidate=False, db_session=None):
        # owning entities have ALL permissions so we return those resources too
        # even without explict perms set
        # TODO: implement admin superrule perm - maybe return all apps
        db_session = self.get_db_session(db_session)
        q = db_session.query(Resource).distinct()
        group_names = [gr.group_name for gr in self.groups]
        #if user has some groups lets try to join based on their permissions
        if group_names:
            join_conditions = (
                          GroupResourcePermission.group_name.in_(group_names),
                          Resource.resource_id == GroupResourcePermission.resource_id,
                          GroupResourcePermission.perm_name.in_(perms),
                          )
            q = q.outerjoin((GroupResourcePermission, sa.and_(*join_conditions),))
            #ensure outerjoin permissions are correct - dont add empty rows from join
            #conditions are - join ON possible group permissions OR owning group/user
            q = q.filter(sa.or_(
                                Resource.owner_user_name == self.user_name,
                                Resource.owner_group_name.in_(group_names),
                                GroupResourcePermission.perm_name != None                                
                                ,))
        else:
            #filter just by username
            q = q.filter(Resource.owner_user_name == self.user_name)
        # lets try by custom user permissions for resource
        q2 = db_session.query(Resource).distinct()
        q2 = q2.filter(UserResourcePermission.user_name == self.user_name)
        q2 = q2.filter(Resource.resource_id == UserResourcePermission.resource_id)
        q2 = q2.filter(UserResourcePermission.perm_name.in_(perms))
        if resource_ids:
            q = q.filter(Resource.resource_id.in_(resource_ids))
        q = q.union(q2)
        q = q.order_by(Resource.resource_name)
        if cache == 'default':
            #cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q
    
    def gravatar_url(self, default='mm'):
        # construct the url
        gravatar_url = "https://secure.gravatar.com/avatar/" \
                        + hashlib.md5(self.email.lower()).hexdigest() + "?"
        gravatar_url += urllib.urlencode({'d':default})
        return gravatar_url
    
    
    def set_password(self, raw_password):
        self.user_password = self.passwordmanager.encode(raw_password)
        self.regenerate_security_code()

    def check_password(self, raw_password):
        return self.passwordmanager.check(self.user_password, raw_password,
                                          setter=self.set_password)

    @classmethod
    def generate_random_pass(cls, chars=7):
        return generate_random_string(chars)
        
    
    def regenerate_security_code(self):      
        crypt = hashlib.sha1('%s%s' % (self.user_name.encode('utf8'), random.random(),))
        self.security_code = crypt.hexdigest()
    
    @classmethod
    def by_user_name(cls, user_name, cache='default',
                    invalidate=False, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls)
        q = q.filter(sa.func.lower(cls.user_name) == user_name.lower())
        if cache == 'default':
            q = q.options(sa.orm.eagerload('groups'))
            #cache = FromCache("default_term", "by_user_name")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q.first()
    
    @classmethod
    def by_user_name_and_security_code(cls, user_name, security_code,
                                       db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls)
        q = q.filter(sa.func.lower(cls.user_name) == user_name.lower())
        q = q.filter(cls.security_code == security_code)
        return q.first()
    
    
    @classmethod
    def by_user_names(cls, user_names, cache='default',
                    invalidate=False, db_session=None):
        user_names = [name.lower() for name in user_names]
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls)
        q = q.filter(sa.func.lower(cls.user_name).in_(user_names))
        if cache == 'default':
            q = q.options(sa.orm.eagerload(User.groups))
            #cache = FromCache("default_term", "by_user_names")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q
    
    @classmethod
    def user_names_like(cls, user_name, cache='default',
                    invalidate=False, db_session=None):
        """ For now rely on LIKE in db - shouldnt be issue ever
        in future we can plug in fulltext search like solr or whoosh
        """
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls)
        q = q.filter(sa.func.lower(cls.user_name).like(user_name.lower()))
        q = q.order_by(cls.user_name)
        if cache == 'default':
            q = q.options(sa.orm.eagerload('groups'))
            #cache = FromCache("default_term", "by_user_names_like")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q

    @classmethod
    def by_email(cls, email, cache='default',
                    invalidate=False, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.email == email)
        if cache == 'default':
            q = q.options(sa.orm.eagerload('groups'))
            #cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q.first()
    
    @classmethod
    def by_email_and_username(cls, email, user_name, cache='default',
                    invalidate=False, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.email == email)
        q = q.filter(sa.func.lower(cls.user_name) == user_name.lower())
        if cache == 'default':
            q = q.options(sa.orm.eagerload('groups'))
            # cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q.first()

class GroupMixin(BaseModel):
    
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    # lists app wide permissions we might want to assign to groups
    __possible_permissions__ = ('root_administration',
                                'administration',
                                'backend_admin_panel',
                                'manage_apps',)
    
    @declared_attr
    def id(cls):
        return sa.Column(sa.Integer, primary_key=True)
    
    @declared_attr
    def group_name(cls):
        return sa.Column(sa.Unicode(50), unique=True)
    
    @declared_attr
    def description(cls):
        return sa.Column(sa.Text())
    
    @declared_attr
    def member_count(cls):
        return sa.Column(sa.Integer, nullable=False, default=0)
    
    @declared_attr
    def users(cls):
        return sa.orm.relationship('User',
                        secondary='users_groups',
                        order_by='User.user_name',
                        passive_deletes=True,
                        passive_updates=True,
                        backref='groups'
                        )
    
    # dynamic property - useful
    @declared_attr
    def users_dynamic(cls):
        return sa.orm.relationship('User',
                        secondary='users_groups',
                        order_by='User.user_name',
                        lazy="dynamic"
                        )
    
    @declared_attr
    def permissions(cls):
        return sa.orm.relationship('GroupPermission',
                        backref='groups',
                        cascade="all, delete-orphan",
                        passive_deletes=True,
                        passive_updates=True
                        )

    @declared_attr
    def resource_permissions(cls):
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
        q = cls.get_db_session(db_session).query(cls)
        return q
    
    @classmethod
    def by_group_name(cls, group_name, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.group_name == group_name)
        return q.first()

    @sa.orm.validates('permissions')
    def validate_permission(self, key, permission):
        assert permission.perm_name in self.__possible_permissions__
        return permission


    def get_user_paginator(self, page=1, item_count=None, items_per_page=50,
                           user_names=None, GET_params={}):
        GET_params.pop('page', None)
        q = self.users_dynamic
        if user_names:
            q = q.filter(UserGroup.user_name.in_(user_names))
        return webhelpers.paginate.Page(q, page=page,
                                     item_count=item_count,
                                     items_per_page=items_per_page,
                                     **GET_params
                                     )
        
    
    
class GroupPermissionMixin(BaseModel):
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    
    @declared_attr
    def group_name(cls):
        return sa.Column(sa.Unicode(50),
                        sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True)
    
    @declared_attr
    def perm_name(cls):
        return sa.Column(sa.Unicode(30), primary_key=True)
    
    def __repr__(self):
        return '<GroupPermission: %s>' % self.perm_name
    
    @classmethod
    def by_group_and_perm(cls, group_name, perm_name, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.group_name == group_name)
        q = q.filter(cls.perm_name == perm_name)
        return q.first()
        
class UserPermissionMixin(BaseModel):
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    
    @declared_attr
    def user_name(cls):
        return sa.Column(sa.Unicode(50),
                         sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)
    @declared_attr
    def perm_name(cls):
        return sa.Column(sa.Unicode(30), primary_key=True)
    
    def __repr__(self):
        return '<UserPermission: %s>' % self.perm_name
    
    @classmethod
    def by_user_and_perm(cls, user_name, perm_name, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.user_name == user_name)
        q = q.filter(cls.perm_name == perm_name)
        return q.first()

class UserGroupMixin(BaseModel):
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    @declared_attr
    def group_name(cls):
        return sa.Column(sa.Unicode(50),
                         sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                       ondelete='CASCADE'), primary_key=True)

    @declared_attr
    def user_name(cls):
        return sa.Column(sa.Unicode(30),
                        sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                      ondelete='CASCADE'), primary_key=True)

    def __repr__(self):
        return '<UserGroup: %s, %s>' % (self.group_name, self.user_name,)

class GroupResourcePermissionMixin(BaseModel):
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    
    @declared_attr
    def group_name(cls):
        return sa.Column(sa.Unicode(50), sa.ForeignKey('groups.group_name',
                                                     onupdate='CASCADE',
                                                     ondelete='CASCADE'),
                                                     primary_key=True)
        
    @declared_attr
    def resource_id(cls):
        return sa.Column(sa.BigInteger(), sa.ForeignKey('resources.resource_id',
                                                     onupdate='CASCADE',
                                                     ondelete='CASCADE'),
                                                     primary_key=True,
                                                     autoincrement=False)
    @declared_attr
    def perm_name(cls):
        return sa.Column(sa.Unicode(50), primary_key=True)

    def __repr__(self):
        return '<GroupResourcePermission: %s, %s, %s>' % (self.group_name,
                                                      self.perm_name,
                                                      self.resource_id,)

class UserResourcePermissionMixin(BaseModel):
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    
    @declared_attr
    def user_name(cls):
        return sa.Column(sa.Unicode(50), sa.ForeignKey('users.user_name',
                                                     onupdate='CASCADE',
                                                     ondelete='CASCADE'),
                                                     primary_key=True)
    @declared_attr
    def resource_id(cls):
        return sa.Column(sa.BigInteger(), sa.ForeignKey('resources.resource_id',
                                                     onupdate='CASCADE',
                                                     ondelete='CASCADE'),
                                                     primary_key=True,
                                                     autoincrement=False)
    @declared_attr
    def perm_name(cls):
        return sa.Column(sa.Unicode(50), primary_key=True)

    def __repr__(self):
        return '<userResourcePermission: %s, %s, %s>' % (self.user_name,
                                                      self.perm_name,
                                                      self.resource_id,)
            
    @classmethod
    def by_resource_user_and_perm(cls, user_name, perm_name, resource_id,
                                  db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.user_name == user_name)
        q = q.filter(cls.resource_id == resource_id)
        q = q.filter(cls.perm_name == perm_name)
        return q.first()
    
#    @classmethod
#    def allowed_permissions(cls, key):
#        """ ensures we can only use permission that can be assigned to this resource type"""
#        if key in cls.__possible_permissions__:
#            return key
#        raise KeyError

class ResourceMapperExtension(sa.orm.interfaces.MapperExtension):
    
    def after_update(self, mapper, connection, instance):
        instance.by_resource_id(instance.resource_id, invalidate=True)
        
    def after_delete(self, mapper, connection, instance):
        instance.by_resource_id(instance.resource_id, invalidate=True)

class ResourceMixin(BaseModel):    
    
    __possible_permissions__ = ()
    
    @declared_attr
    def resource_id(cls):
        return sa.Column(sa.BigInteger(), primary_key=True)
    
    @declared_attr
    def resource_name(cls):
        return sa.Column(sa.Unicode(100), nullable=False)
    
    @declared_attr
    def resource_type(cls):
        return sa.Column(sa.Unicode(30), nullable=False)
    
    @declared_attr
    def owner_group_name(cls):
        return sa.Column(sa.Unicode(50),
                       sa.ForeignKey('groups.group_name', onupdate='CASCADE',
                                     ondelete='SET NULL'))
    
    @declared_attr
    def owner_user_name(cls):
        return sa.Column(sa.Unicode(30),
                       sa.ForeignKey('users.user_name', onupdate='CASCADE',
                                     ondelete='SET NULL'))
    
    @declared_attr
    def group_permissions(cls):
        return sa.orm.relationship('GroupResourcePermission',
                                  cascade="all, delete-orphan",
                                  passive_deletes=True,
                                  passive_updates=True
                                  )

    @declared_attr
    def user_permissions(cls):
        return sa.orm.relationship('UserResourcePermission',
                                  cascade="all, delete-orphan",
                                  passive_deletes=True,
                                  passive_updates=True
                                  )
    
    @declared_attr
    def groups(cls):
        return sa.orm.relationship('Group',
                                 secondary='groups_resources_permissions',
                                 passive_deletes=True,
                                 passive_updates=True
                                  )
    
    @declared_attr
    def users(cls):
        return sa.orm.relationship('User',
                                 secondary='users_resources_permissions',
                                 passive_deletes=True,
                                 passive_updates=True
                                  )
    
    __mapper_args__ = {'polymorphic_on': resource_type,
                       'extension': ResourceMapperExtension()
                       }
    __table_args__ = {
                      'mysql_engine':'InnoDB',
                      'mysql_charset':'utf8'
                      }
    
    def __repr__(self):
        return '<Resource: %s, %s, id: %s>' % (self.resource_type,
                                               self.resource_name,
                                               self.resource_id,
                                               )
        
    @property
    def __acl__(self):
        acls = [(Allow, 'group:Administrators', ALL_PERMISSIONS,), ]
        
        if self.owner_user_name:
            acls.extend([(Allow, self.owner_user_name, ALL_PERMISSIONS,), ])
            
        if self.owner_group_name:
            acls.extend([(Allow, self.owner_group_name, ALL_PERMISSIONS,), ])
        return acls
    
    def perms_for_user(self, user, cache='default',
                       invalidate=False, db_session=None):
        db_session = self.get_db_session(db_session)
        q = db_session.query('group:' + GroupResourcePermission.group_name, GroupResourcePermission.perm_name)
        q = q.filter(GroupResourcePermission.group_name.in_([gr.group_name for gr in user.groups]))
        q = q.filter(GroupResourcePermission.resource_id == self.resource_id)
        
        q2 = db_session.query(UserResourcePermission.user_name, UserResourcePermission.perm_name)
        q2 = q2.filter(UserResourcePermission.user_name == user.user_name)
        q2 = q2.filter(UserResourcePermission.resource_id == self.resource_id)
        q = q.union(q2)
        if cache == 'default':
            # cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q
    
    
    def direct_perms_for_user(self, user, cache='default',
                       invalidate=False, db_session=None):
        db_session = self.get_db_session(db_session)
        q = db_session.query(UserResourcePermission.user_name, UserResourcePermission.perm_name)
        q = q.filter(UserResourcePermission.user_name == user.user_name)
        q = q.filter(UserResourcePermission.resource_id == self.resource_id)
        if cache == 'default':
            # cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q

    def group_perms_for_user(self, user, cache='default',
                       invalidate=False, db_session=None):
        db_session = self.get_db_session(db_session)
        q = db_session.query('group:' + GroupResourcePermission.group_name, GroupResourcePermission.perm_name)
        q = q.filter(GroupResourcePermission.group_name.in_([gr.group_name for gr in user.groups]))
        q = q.filter(GroupResourcePermission.resource_id == self.resource_id)
        if cache:
            # cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q
    
    
    def users_for_perm(self, perm_name, cache='default',
                       invalidate=False, db_session=None):
        db_session = self.get_db_session(db_session)
        q = db_session.query(User, GroupResourcePermission.perm_name)
        q = q.filter(User.user_name == UserGroup.user_name)
        q = q.filter(UserGroup.user_name == GroupResourcePermission.group_name)
        if perm_name != '__any_permission__':
            q = q.filter(GroupResourcePermission.perm_name == perm_name)
        q = q.filter(GroupResourcePermission.resource_id == self.resource_id)        
        q2 = db_session.query(User, UserResourcePermission.perm_name)
        q2 = q2.filter(User.user_name == UserResourcePermission.user_name)
        if perm_name != '__any_permission__':
            q2 = q2.filter(UserResourcePermission.perm_name == perm_name)
        q2 = q2.filter(UserResourcePermission.resource_id == self.resource_id)
        q = q.union(q2)
        if cache == 'default':
            # cache = FromCache("default_term", "by_perm")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q
        
    @classmethod
    def by_resource_id(cls, resource_id, cache='default',
                       invalidate=False, db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(cls).filter(cls.resource_id == int(resource_id))
        if cache:
            # cache = FromCache("default_term", "by_id")
            pass #q = q.options(cache)
        elif cache:
            pass #q = q.options(cache)
        if invalidate:
            pass #q.invalidate()
            return True
        return q.first()
    
    @classmethod
    def all(cls):
        q = cls.get_db_session(db_session).query(cls)
        return q
    
    @classmethod
    def perm_by_group_and_perm_name(cls, res_id, group_name, perm_name,
                                    db_session=None):
        db_session = cls.get_db_session(db_session)
        q = db_session.query(GroupResourcePermission)
        q = q.filter(GroupResourcePermission.group_name == group_name)
        q = q.filter(GroupResourcePermission.perm_name == perm_name)
        q = q.filter(GroupResourcePermission.resource_id == res_id)
        return q.first()
    
    @sa.orm.validates('user_permissions') 
    @sa.orm.validates('group_permissions')
    def validate_permission(self, key, permission):
        assert permission.perm_name in self.__possible_permissions__
        return permission
