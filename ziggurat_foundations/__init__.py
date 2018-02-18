# -*- coding: utf-8 -*-
from __future__ import unicode_literals

__version__ = {'major': 0, 'minor': 7, 'patch': 2}


class ModelProxy(object):
    pass


class NOOP(object):
    def __nonzero__(self):
        return False

        # py3 compat

    __bool__ = __nonzero__


noop = NOOP()


def make_passwordmanager(schemes=None):
    """
        schemes contains a list of replace this list with the hash(es) you wish to support.
        this example sets pbkdf2_sha256 as the default,
        with support for legacy bcrypt hashes.
    :param schemes:
    :return: CryptContext()
    """
    from passlib.context import CryptContext
    if not schemes:
        schemes = ["pbkdf2_sha256", "bcrypt"]
    pwd_context = CryptContext(
        schemes=schemes,
        deprecated="auto"
    )
    return pwd_context


def ziggurat_model_init(*args, **kwargs):
    """
    This function handles attaching model to service if model has one specified
    as `_ziggurat_service`, Also attached a proxy object holding all model
    definitions that services might use

    :param args:
    :param kwargs:
    :param passwordmanager, the password manager to override default one
    :param passwordmanager_schemes, list of schemes for default passwordmanager to use
    :return:
    """
    models = ModelProxy()
    for cls2 in args:
        setattr(models, cls2.__name__, cls2)

    for cls in args:
        if cls.__name__ == 'User':
            if kwargs.get('passwordmanager'):
                cls.passwordmanager = kwargs['passwordmanager']
            else:
                cls.passwordmanager = make_passwordmanager(kwargs.get('passwordmanager_schemes'))

        for cls2 in args:
            setattr(models, cls2.__name__, cls2)
        setattr(cls, "_ziggurat_models", models)
        # if model has a manager attached attached the class also to manager
        if hasattr(cls, '_ziggurat_services'):
            for service in cls._ziggurat_services:
                setattr(service, 'model', cls)
                setattr(service, 'models_proxy', models)
