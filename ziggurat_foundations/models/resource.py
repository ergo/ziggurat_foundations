# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr

from ziggurat_foundations.exc import ZigguratException
from ziggurat_foundations.models.base import BaseModel

__all__ = ["ResourceMixin"]


class ResourceMixin(BaseModel):
    """
    Mixin for Resource model
    """

    __possible_permissions__ = ()

    @declared_attr
    def __tablename__(self):
        return "resources"

    @declared_attr
    def resource_id(self):
        return sa.Column(
            sa.Integer(), primary_key=True, nullable=False, autoincrement=True
        )

    @declared_attr
    def parent_id(self):
        return sa.Column(
            sa.Integer(),
            sa.ForeignKey(
                "resources.resource_id", onupdate="CASCADE", ondelete="SET NULL"
            ),
        )

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
        return sa.Column(
            sa.Integer,
            sa.ForeignKey("groups.id", onupdate="CASCADE", ondelete="SET NULL"),
            index=True,
        )

    @declared_attr
    def owner_user_id(self):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="SET NULL"),
            index=True,
        )

    @declared_attr
    def group_permissions(self):
        """ returns all group permissions for this resource"""
        return sa.orm.relationship(
            "GroupResourcePermission",
            cascade="all, delete-orphan",
            passive_deletes=True,
            passive_updates=True,
        )

    @declared_attr
    def user_permissions(self):
        """ returns all user permissions for this resource"""
        return sa.orm.relationship(
            "UserResourcePermission",
            cascade="all, delete-orphan",
            passive_deletes=True,
            passive_updates=True,
        )

    @declared_attr
    def groups(self):
        """ returns all groups that have permissions for this resource"""
        return sa.orm.relationship(
            "Group",
            secondary="groups_resources_permissions",
            passive_deletes=True,
            passive_updates=True,
        )

    @declared_attr
    def users(self):
        """ returns all users that have permissions for this resource"""
        return sa.orm.relationship(
            "User",
            secondary="users_resources_permissions",
            passive_deletes=True,
            passive_updates=True,
        )

    __mapper_args__ = {"polymorphic_on": resource_type}
    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8"}

    def __repr__(self):
        return "<Resource: %s, %s, id: %s position: %s>" % (
            self.resource_type,
            self.resource_name,
            self.resource_id,
            self.ordering,
        )

    @property
    def __acl__(self):
        raise ZigguratException("Model should implement __acl__")

    @sa.orm.validates("user_permissions", "group_permissions")
    def validate_permission(self, key, permission):
        """ validate if resource can have specific permission """
        if permission.perm_name not in self.__possible_permissions__:
            raise AssertionError(
                "perm_name is not one of {}".format(self.__possible_permissions__)
            )
        return permission
