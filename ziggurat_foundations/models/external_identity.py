# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from zope.deprecation import deprecation

from ziggurat_foundations.models.base import BaseModel
from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services.external_identity import \
    ExternalIdentityService

__all__ = ['ExternalIdentityMixin']


class ExternalIdentityMixin(BaseModel):
    """
    Mixin for External Identity model - it represents oAuth(or other) accounts
    attached to your user object
    """

    __table_args__ = (
        sa.PrimaryKeyConstraint('external_id', 'local_user_id', 'provider_name',
                                name='pk_external_identities'),
        {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8',
         })

    _ziggurat_services = [ExternalIdentityService]

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
    def local_user_id(self):
        return sa.Column(sa.Integer, sa.ForeignKey('users.id',
                                                   onupdate='CASCADE',
                                                   ondelete='CASCADE'),
                         primary_key=True)

    @declared_attr
    def provider_name(self):
        return sa.Column(sa.Unicode(50), default=u'', primary_key=True)

    @declared_attr
    def access_token(self):
        return sa.Column(sa.Unicode(512), default=u'')

    @declared_attr
    def alt_token(self):
        return sa.Column(sa.Unicode(512), default=u'')

    @declared_attr
    def token_secret(self):
        return sa.Column(sa.Unicode(512), default=u'')

    @classmethod
    @deprecation.deprecate("ExternalIdentity.by_external_id_and_provider "
                           "will be removed in 0.8, use service instead")
    def by_external_id_and_provider(cls, external_id, provider_name,
                                    db_session=None):
        """
        Backwards compatible alias to
        :class:`ziggurat_foundations.models.services.external_identity.ExternalIdentityService.by_external_id_and_provider`

        .. deprecated:: 0.8

        :param external_id:
        :param provider_name:
        :param db_session:
        :return: ExternalIdentity
        """
        db_session = get_db_session(db_session)
        return ExternalIdentityService.by_external_id_and_provider(
            external_id=external_id, provider_name=provider_name,
            db_session=db_session)

    @classmethod
    @deprecation.deprecate("ExternalIdentity.user_by_external_id_and_provider "
                           "will be removed in 0.8, use service instead")
    def user_by_external_id_and_provider(cls, external_id, provider_name,
                                         db_session=None):
        """
        Backwards compatible alias to
        :class:`ziggurat_foundations.models.services.external_identity.ExternalIdentityService.user_by_external_id_and_provider`

        .. deprecated:: 0.8

        :param external_id:
        :param provider_name:
        :param db_session:
        :return: User
        """
        db_session = get_db_session(db_session)
        return ExternalIdentityService.user_by_external_id_and_provider(
            external_id=external_id, provider_name=provider_name,
            db_session=db_session)
