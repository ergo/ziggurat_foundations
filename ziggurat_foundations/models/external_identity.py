# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr

from ziggurat_foundations.models.base import BaseModel


__all__ = ["ExternalIdentityMixin"]


class ExternalIdentityMixin(BaseModel):
    """
    Mixin for External Identity model - it represents oAuth(or other) accounts
    attached to your user object
    """

    __table_args__ = (
        sa.PrimaryKeyConstraint(
            "external_id",
            "local_user_id",
            "provider_name",
            name="pk_external_identities",
        ),
        {"mysql_engine": "InnoDB", "mysql_charset": "utf8"},
    )

    @declared_attr
    def __tablename__(self):
        return "external_identities"

    @declared_attr
    def external_id(self):
        return sa.Column(sa.Unicode(255), default="", primary_key=True)

    @declared_attr
    def external_user_name(self):
        return sa.Column(sa.Unicode(255), default="")

    @declared_attr
    def local_user_id(self):
        return sa.Column(
            sa.Integer,
            sa.ForeignKey("users.id", onupdate="CASCADE", ondelete="CASCADE"),
            primary_key=True,
        )

    @declared_attr
    def provider_name(self):
        return sa.Column(sa.Unicode(50), default="", primary_key=True)

    @declared_attr
    def access_token(self):
        return sa.Column(sa.Unicode(512), default="")

    @declared_attr
    def alt_token(self):
        return sa.Column(sa.Unicode(512), default="")

    @declared_attr
    def token_secret(self):
        return sa.Column(sa.Unicode(512), default="")
