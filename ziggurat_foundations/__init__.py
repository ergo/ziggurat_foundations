from __future__ import unicode_literals

__version__ = {'major': 0, 'minor': 6, 'patch': 8}


class ModelProxy(object):
    pass


def make_passwordmanager():
    from passlib.context import CryptContext
    pwd_context = CryptContext(
        # replace this list with the hash(es) you wish to support.
        # this example sets pbkdf2_sha256 as the default,
        # with support for legacy des_crypt hashes.
        schemes=["bcrypt"],
        default="bcrypt"
    )
    return pwd_context


def ziggurat_model_init(*k, **kw):
    """
    This function handles attaching model to service if model has one specified
    as `_ziggurat_service`, Also attached a proxy object holding all model
    definitions that services might use

    :param k:
    :param kw:
    :return:
    """
    models = ModelProxy()
    for cls2 in k:
        setattr(models, cls2.__name__, cls2)

    for cls in k:
        if cls.__name__ == 'User':
            if kw.get('passwordmanager'):
                cls.passwordmanager = kw['passwordmanager']
            else:
                cls.passwordmanager = make_passwordmanager()

        for cls2 in k:
            setattr(models, cls2.__name__, cls2)
        setattr(cls, "_ziggurat_models", models)
        # if model has a manager attached attached the class also to manager
        if hasattr(cls, '_ziggurat_service'):
            setattr(cls._ziggurat_service, 'model', cls)
            setattr(cls._ziggurat_service, 'models_proxy', models)
