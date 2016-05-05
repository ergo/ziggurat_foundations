from __future__ import unicode_literals
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel
from .services.user import UserService
from .base import get_db_session


class UserMixin(BaseModel):
    """ Base mixin for user object representation.
        It supplies all the basic functionality from password hash generation
        and matching to utility methods used for querying database for users
        and their permissions or resources they have access to. It is meant
        to be extended with other application specific properties"""

    __mapper_args__ = {}
    __table_args__ = {'mysql_engine': 'InnoDB',
                      'mysql_charset': 'utf8'}

    _ziggurat_service = UserService

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
        return sa.Column(sa.Unicode(128), unique=True)

    @declared_attr
    def user_password(self):
        """ Password hash for user object """
        return sa.Column(sa.Unicode(256))

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
        return sa.Column(sa.Unicode(256), default='default')

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
                                   passive_updates=True)

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

    @property
    def permissions(self):
        db_session = get_db_session(None, self)
        return UserService.permissions(self, db_session=db_session)

    def resources_with_perms(self, perms, resource_ids=None,
                             resource_types=None,
                             db_session=None):
        db_session = get_db_session(db_session, self)
        return UserService.resources_with_perms(
            self, perms=perms, resource_ids=resource_ids,
            resource_types=resource_types, db_session=db_session)

    def groups_with_resources(self):
        return UserService.groups_with_resources(self)

    def resources_with_possible_perms(self, resource_ids=None,
                                      resource_types=None,
                                      db_session=None):
        db_session = get_db_session(db_session, self)
        return UserService.resources_with_possible_perms(
            self, resource_ids=resource_ids, resource_types=resource_types,
            db_session=db_session)

    def gravatar_url(self, default='mm', **kwargs):
        return UserService.gravatar_url(self, default, **kwargs)

    def set_password(self, raw_password):
        return UserService.set_password(self, raw_password=raw_password)

    def check_password(self, raw_password):
        return UserService.check_password(self, raw_password=raw_password)

    @classmethod
    def migrate_password(self, raw_password):
        pass

    @classmethod
    def generate_random_pass(cls, chars=7):
        return UserService.generate_random_pass(chars=chars)

    def regenerate_security_code(self):
        return UserService.regenerate_security_code(self)

    @staticmethod
    def generate_random_string(chars=7):
        return UserService.generate_random_pass(chars=chars)

    @classmethod
    def by_id(cls, user_id, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.by_id(user_id=user_id, db_session=db_session)

    @classmethod
    def by_user_name(cls, user_name, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.by_user_name(user_name=user_name,
                                        db_session=db_session)

    @classmethod
    def by_user_name_and_security_code(cls, user_name, security_code,
                                       db_session=None):
        db_session = get_db_session(db_session)
        return UserService.by_user_name_and_security_code(
            user_name=user_name, security_code=security_code,
            db_session=db_session)

    @classmethod
    def by_user_names(cls, user_names, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.by_user_names(user_names=user_names,
                                         db_session=db_session)

    @classmethod
    def user_names_like(cls, user_name, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.user_names_like(user_name=user_name,
                                           db_session=db_session)

    @classmethod
    def by_email(cls, email, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.by_email(email=email,
                                    db_session=db_session)

    @classmethod
    def by_email_and_username(cls, email, user_name, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.by_email_and_username(email=email,
                                                 user_name=user_name,
                                                 db_session=db_session)

    @classmethod
    def users_for_perms(cls, perm_names, db_session=None):
        db_session = get_db_session(db_session)
        return UserService.users_for_perms(perm_names=perm_names,
                                           db_session=db_session)
