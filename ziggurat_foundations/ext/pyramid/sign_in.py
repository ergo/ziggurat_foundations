# -*- coding: utf-8 -*-
import pyramid.security
import logging

CONFIG_KEY = 'ziggurat_foundations'
log = logging.getLogger(__name__)


class ZigguratSignInSuccess(object):

    def __contains__(self, other):
        return True

    def __init__(self, headers, came_from, user):
        self.headers = headers
        self.came_from = came_from
        self.user = user


class ZigguratSignInBadAuth(object):

    def __contains__(self, other):
        return False

    def __init__(self, headers, came_from):
        self.headers = headers
        self.came_from = came_from


class ZigguratSignOut(object):

    def __contains__(self, other):
        return True

    def __init__(self, headers):
        self.headers = headers


def includeme(config):
    settings = config.registry.settings
    sign_in_path = settings.get('%s.sign_in.sign_in_pattern' % CONFIG_KEY,
                                '/sign_in')
    sign_out_path = settings.get('%s.sign_in.sign_out_pattern' % CONFIG_KEY,
                                 '/sign_out')
    user_model_location = settings.get('%s.model_locations.User' % CONFIG_KEY)
    signin_came_from_key = settings.get('%s.sign_in.came_from_key' %
                                        CONFIG_KEY, 'came_from')
    signin_username_key = settings.get('%s.sign_in.username_key' %
                                       CONFIG_KEY, 'login')
    signin_password_key = settings.get('%s.sign_in.password_key' %
                                       CONFIG_KEY, 'password')

    if not user_model_location:
        raise Exception('''You need to pass location of user model
        inside your application eg.:
        ziggurat_foundations.user_model_location = youappname.models:User
        ''')

    parts = user_model_location.split(':')
    _tmp = __import__(parts[0], globals(), locals(), [parts[1], ], 0)
    UserModel = getattr(_tmp, parts[1])

    endpoint = ZigguratSignInProvider(settings=settings,
                                      UserModel=UserModel,
                                      signin_came_from_key=signin_came_from_key,
                                      signin_username_key=signin_username_key,
                                      signin_password_key=signin_password_key
                                      )
    config.add_route('ziggurat.routes.sign_in', sign_in_path,
                     use_global_views=True,
                     factory=endpoint.sign_in)
    config.add_route('ziggurat.routes.sign_out', sign_out_path,
                     use_global_views=True,
                     factory=endpoint.sign_out)


class ZigguratSignInProvider(object):

    def __init__(self, *args, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def sign_in(self, request):
        came_from = request.params.get(self.signin_came_from_key, '/')
        user = self.UserModel.by_user_name(
            request.params.get(self.signin_username_key))
        if user == None:
            # if no result, test to see if email exists
            user = self.UserModel.by_email(
                request.params.get(self.signin_username_key))
        if user:
            password = request.params.get(self.signin_password_key)
            if user.check_password(password):
                headers = pyramid.security.remember(request, user.id)
                return ZigguratSignInSuccess(headers=headers,
                                             came_from=came_from, user=user)


        headers = pyramid.security.forget(request)
        return ZigguratSignInBadAuth(headers=headers, came_from=came_from)

    def sign_out(self, request):
        headers = pyramid.security.forget(request)
        return ZigguratSignOut(headers=headers)
