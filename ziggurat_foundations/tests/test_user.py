# -*- coding: utf-8 -*-
from __future__ import with_statement, unicode_literals

import six

from ziggurat_foundations.models.services.user import UserService
from ziggurat_foundations.tests import BaseTestCase, add_user
from ziggurat_foundations.tests.conftest import (User)


class TestUser(BaseTestCase):
    def test_get(self, db_session):
        org_user = add_user(db_session)
        user = UserService.get(user_id=org_user.id, db_session=db_session)
        assert org_user.id == user.id

    def test_add_user(self, db_session):
        user = User(user_name='username', email='email', status=0)
        db_session.add(user)
        db_session.flush()

        user = db_session.query(User).filter(User.user_name == 'username')
        user = user.first()
        assert user.user_name == 'username'
        assert user.email == 'email'
        assert user.status == 0

    def test_delete_user(self, db_session):
        add_user(db_session)
        to_delete = User.by_user_name('username', db_session=db_session)
        db_session.delete(to_delete)
        db_session.commit()

    def test_user_repr(self, db_session):
        user = add_user(db_session)
        assert repr(user) == '<User: username>'

    def test_check_password_correct(self, db_session):
        user = add_user(db_session)
        assert user.check_password('password') is True

    def test_check_password_wrong(self, db_session):
        user = add_user(db_session)
        assert user.check_password('wrong_password') is False

    def test_by_user_name_existing(self, db_session):
        created_user = add_user(db_session)
        queried_user = User.by_user_name('username', db_session=db_session)

        assert created_user == queried_user

    def test_by_user_name_not_existing(self, db_session):
        add_user(db_session)
        queried_user = User.by_user_name('not_existing_user',
                                         db_session=db_session)

        assert queried_user is None

    def test_by_user_name_none(self, db_session):
        queried_user = User.by_user_name(None, db_session=db_session)

        assert queried_user is None

    def test_by_username_andsecurity_code_existing(self, db_session):
        created_user = add_user(db_session)
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name='username',
            security_code=security_code,
            db_session=db_session
        )

        assert created_user == queried_user

    def test_by_username_andsecurity_code_not_existing(self, db_session):
        created_user = add_user(db_session)
        security_code = created_user.security_code
        queried_user = User.by_user_name_and_security_code(
            user_name='not_existing_user',
            security_code=security_code,
            db_session=db_session
        )

        assert queried_user is None

    def test_by_username_andsecurity_code_wrong_code(self, db_session):
        add_user(db_session)
        queried_user = User.by_user_name_and_security_code(
            user_name='username',
            security_code='wrong_code',
            db_session=db_session
        )

        assert queried_user is None

    def test_by_username_andsecurity_code_none(self, db_session):
        created_user = add_user(db_session)
        security_code = created_user.security_code
        found = User.by_user_name_and_security_code(
            user_name=None,
            security_code=security_code,
            db_session=db_session
        )

        assert found is None

    def test_by_user_names(self, db_session):
        user1 = add_user(db_session, 'user1', 'email1')
        add_user(db_session, 'user2', 'email2')
        user3 = add_user(db_session, 'user3', 'email3')

        queried_users = User.by_user_names(['user1', 'user3'],
                                           db_session=db_session).all()

        assert len(queried_users) == 2
        assert user1 == queried_users[0]
        assert user3 == queried_users[1]

    def test_by_user_names_one_none(self, db_session):
        user1 = add_user(db_session, 'user1', 'email1')
        add_user(db_session, 'user2', 'email2')
        user3 = add_user(db_session, 'user3', 'email3')

        queried_users = User.by_user_names(['user1', None, 'user3'],
                                           db_session=db_session).all()

        assert len(queried_users) == 2
        assert user1 == queried_users[0]
        assert user3 == queried_users[1]

    def test_by_user_names_like(self, db_session):
        user1 = add_user(db_session, 'user1', 'email1')
        add_user(db_session, 'luser2', 'email2')
        add_user(db_session, 'noname', 'email3')

        queried_users = User.user_names_like('user%',
                                             db_session=db_session).all()
        assert len(queried_users) == 1
        assert user1 == queried_users[0]

    def test_by_user_names_like_none(self, db_session):
        queried_users = User.user_names_like(None,
                                             db_session=db_session).all()
        assert [] == queried_users

    def test_by_email(self, db_session):
        created_user = add_user(db_session)
        queried_user = User.by_email('email', db_session=db_session)

        assert created_user == queried_user

    def test_by_email_none(self, db_session):
        add_user(db_session)
        queried_user = User.by_email(None, db_session=db_session)

        assert queried_user is None

    def test_by_email_wrong_email(self, db_session):
        add_user(db_session)
        queried_user = User.by_email('wrong_email', db_session=db_session)

        assert queried_user is None

    def test_by_mail_and_username(self, db_session):
        created_user = add_user(db_session)
        queried_user = User.by_email_and_username('email', 'username',
                                                  db_session=db_session)

        assert created_user == queried_user

    def test_by_mail_and_username_wrong_mail(self, db_session):
        add_user(db_session)
        queried_user = User.by_email_and_username('wrong_email', 'username',
                                                  db_session=db_session)

        assert queried_user is None

    def test_by_mail_and_username_wrong_username(self, db_session):
        add_user(db_session)
        queried_user = User.by_email_and_username('email', 'wrong_username',
                                                  db_session=db_session)

        assert queried_user is None

    def test_by_mail_and_username_none(self, db_session):
        found = User.by_email_and_username('email', None,
                                           db_session=db_session)
        assert found is None

    def test_gravatar_url(self, db_session):
        user = add_user(db_session)
        user.email = 'arkadiy@bk.ru'
        assert user.gravatar_url() == 'https://secure.gravatar.com/avatar/' \
                                      'cbb6777e4a7ec0d96b33d2033e59fec6?d=mm'

    def test_gravatar_url_with_params(self, db_session):
        import six.moves.urllib.parse as parser
        user = add_user(db_session)
        user.email = 'arkadiy@bk.r'
        gravatar_url = user.gravatar_url(s=100, r='pg')
        parsed_url = parser.urlparse(gravatar_url)
        qs_dict = parser.parse_qs(parsed_url.query)
        assert qs_dict == {'s': ['100'], 'd': ['mm'], 'r': ['pg']}

    def test_generate_random_string(self, db_session):
        rand_str = User.generate_random_string()

        assert len(rand_str) == 7
        assert isinstance(rand_str, six.string_types)

    def test_generate_random_pass(self, db_session):
        rand_str = User.generate_random_pass()

        assert len(rand_str) == 7
        assert isinstance(rand_str, six.string_types)

        rand_str = User.generate_random_pass(20)
        assert len(rand_str) == 20

    def test_regenerate_security_code(self, db_session):
        created_user = add_user(db_session)
        old_code = created_user.security_code
        created_user.regenerate_security_code()
        new_code = created_user.security_code

        assert old_code != new_code
        assert len(new_code) == 64
