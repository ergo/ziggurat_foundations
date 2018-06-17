# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr

from ziggurat_foundations.models.base import BaseModel


__all__ = ["GroupMixin"]


class GroupMixin(BaseModel):
    """ Mixin for Group model """

    __table_args__ = {"mysql_engine": "InnoDB", "mysql_charset": "utf8"}

    @declared_attr
    def __tablename__(self):
        return "groups"

    # lists app wide permissions we might want to assign to groups
    __possible_permissions__ = ()

    @declared_attr
    def id(self):
        return sa.Column(sa.Integer(), primary_key=True)

    @declared_attr
    def group_name(self):
        return sa.Column(sa.Unicode(128), nullable=False, unique=True)

    @declared_attr
    def description(self):
        return sa.Column(sa.Text())

    @declared_attr
    def member_count(self):
        return sa.Column(sa.Integer, nullable=False, default=0)

    @declared_attr
    def users(self):
        """ relationship for users belonging to this group"""
        return sa.orm.relationship(
            "User",
            secondary="users_groups",
            order_by="User.user_name",
            passive_deletes=True,
            passive_updates=True,
            backref="groups",
        )

    # dynamic property - useful
    @declared_attr
    def users_dynamic(self):
        """ dynamic relationship for users belonging to this group
            one can use filter """
        return sa.orm.relationship(
            "User", secondary="users_groups", order_by="User.user_name", lazy="dynamic"
        )

    @declared_attr
    def permissions(self):
        """ non-resource permissions assigned to this group"""
        return sa.orm.relationship(
            "GroupPermission",
            backref="groups",
            cascade="all, delete-orphan",
            passive_deletes=True,
            passive_updates=True,
        )

    @declared_attr
    def resource_permissions(self):
        """ permissions to specific resources this group has"""
        return sa.orm.relationship(
            "GroupResourcePermission",
            backref="groups",
            cascade="all, delete-orphan",
            passive_deletes=True,
            passive_updates=True,
        )

    @declared_attr
    def resources(self):
        """ Returns all resources directly owned by group, can be used to assign
        ownership of new resources::

            user.resources.append(resource) """
        return sa.orm.relationship(
            "Resource",
            cascade="all",
            passive_deletes=True,
            passive_updates=True,
            backref="owner_group",
        )

    @declared_attr
    def resources_dynamic(self):
        """ Returns all resources directly owned by group, can be used to assign
        ownership of new resources::

            user.resources.append(resource) """
        return sa.orm.relationship(
            "Resource",
            cascade="all",
            passive_deletes=True,
            passive_updates=True,
            lazy="dynamic",
        )

    @sa.orm.validates("permissions")
    def validate_permission(self, key, permission):
        """ validates if group can get assigned with permission"""
        if permission.perm_name not in self.__possible_permissions__:
            raise AssertionError(
                "perm_name is not one of {}".format(self.__possible_permissions__)
            )
        return permission

    def __repr__(self):
        return "<Group: %s, %s>" % (self.group_name, self.id)
