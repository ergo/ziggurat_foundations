# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import importlib
import logging

from ziggurat_foundations.models.base import get_db_session
from ziggurat_foundations.models.services.user import UserService

CONFIG_KEY = "ziggurat_foundations"
log = logging.getLogger(__name__)


def includeme(config):
    settings = config.registry.settings

    session_provider_callable_config = settings.get(
        "%s.session_provider_callable" % CONFIG_KEY
    )
    try_global_session = False

    if not session_provider_callable_config:

        def session_provider_callable(request):
            return get_db_session()

        try_global_session = True
    else:
        if callable(session_provider_callable_config):
            session_provider_callable = session_provider_callable_config
        else:
            parts = session_provider_callable_config.split(":")
            _tmp = importlib.import_module(parts[0])
            session_provider_callable = getattr(_tmp, parts[1])

    # This function is bundled into the request, so for each request you can
    # do request.user
    def get_user(request):
        userid = request.unauthenticated_userid
        if try_global_session:
            # set db_session to none to pass to the UserModel.by_id so it can try to autodiscover
            db_session = None
        else:
            # Else assign the request.session
            db_session = session_provider_callable(request)
        if userid is not None:
            return UserService.by_id(userid, db_session=db_session)

    # add in request.user function
    config.add_request_method(get_user, "user", reify=True, property=True)
