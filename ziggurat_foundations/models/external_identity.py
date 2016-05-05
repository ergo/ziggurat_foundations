from __future__ import unicode_literals
import sqlalchemy as sa
from sqlalchemy.ext.declarative import declared_attr
from .base import BaseModel
from .services.external_identity import ExternalIdentityService
from .base import get_db_session


class ExternalIdentityMixin(BaseModel):
    __table_args__ = {'mysql_engine': 'InnoDB', 'mysql_charset': 'utf8'}

    _ziggurat_service = ExternalIdentityService

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
    def by_external_id_and_provider(cls, external_id, provider_name,
                                    db_session=None):
        """
        Backwards compatible alias to
        :class:`ziggurat_foundations.models.services.external_identity.ExternalIdentityService.by_external_id_and_provider`

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
    def user_by_external_id_and_provider(cls, external_id, provider_name,
                                         db_session=None):
        """
        Backwards compatible alias to
        :class:`ziggurat_foundations.models.services.external_identity.ExternalIdentityService.user_by_external_id_and_provider`

        :param external_id:
        :param provider_name:
        :param db_session:
        :return: User
        """
        db_session = get_db_session(db_session)
        return ExternalIdentityService.user_by_external_id_and_provider(
            external_id=external_id, provider_name=provider_name,
            db_session=db_session)
