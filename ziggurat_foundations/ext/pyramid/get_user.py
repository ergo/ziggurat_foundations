from __future__ import unicode_literals
import logging
import importlib

from ziggurat_foundations.models.base import get_db_session
from pyramid.security import unauthenticated_userid

CONFIG_KEY = 'ziggurat_foundations'
log = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings

    user_model_location = settings.get('%s.model_locations.User' % CONFIG_KEY)
    session_provider_callable = settings.get(
        '%s.session_provider_callable' % CONFIG_KEY)

    if not user_model_location:
        raise Exception('''You need to pass location of user model
        inside your application eg.:
        ziggurat_foundations.user_model_location = youappname.models:User
        ''')

    if not session_provider_callable:
        def session_provider_callable(request):
            return get_db_session()

        test_session_callable = None
    else:
        parts = session_provider_callable.split(':')
        _tmp = importlib.import_module(parts[0])
        session_provider_callable = getattr(_tmp, parts[1])
        test_session_callable = "session exists"

    parts = user_model_location.split(':')
    _tmp = importlib.import_module(parts[0])
    UserModel = getattr(_tmp, parts[1])

    # This function is bundled into the request, so for each request you can 
    # do request.user
    def get_user(request):
        userid = unauthenticated_userid(request)
        if test_session_callable == None:
            # set db_session to none to pass to the UserModel.by_id
            db_session = None
        else:
            # Else assign the request.session
            db_session = session_provider_callable(request)
        if userid is not None:
            return UserModel.by_id(userid, db_session=db_session)

    # add in request.user function
    config.set_request_property(get_user, 'user', reify=True)
