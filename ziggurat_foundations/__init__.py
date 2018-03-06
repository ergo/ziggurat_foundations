# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from ziggurat_foundations.utils import ModelProxy, noop  # noqa

__version__ = {'major': 0, 'minor': 8, 'patch': 0}


def import_model_service_mappings():
    from ziggurat_foundations.models.services.user import UserService
    from ziggurat_foundations.models.services.group import GroupService
    from ziggurat_foundations.models.services.group_permission import \
        GroupPermissionService
    from ziggurat_foundations.models.services.user_permission import \
        UserPermissionService
    from ziggurat_foundations.models.services.user_resource_permission import \
        UserResourcePermissionService
    from ziggurat_foundations.models.services.group_resource_permission import GroupResourcePermissionService  # noqa
    from ziggurat_foundations.models.services.resource import ResourceService
    from ziggurat_foundations.models.services.resource_tree import \
        ResourceTreeService
    from ziggurat_foundations.models.services.external_identity import \
        ExternalIdentityService

    return {
        'User': [UserService],
        'Group': [GroupService],
        'GroupPermission': [GroupPermissionService],
        'UserPermission': [UserPermissionService],
        'UserResourcePermission': [
            UserResourcePermissionService],
        'GroupResourcePermission': [
            GroupResourcePermissionService],
        'Resource': [ResourceService, ResourceTreeService],
        'ExternalIdentity': [ExternalIdentityService]
    }


def make_passwordmanager(schemes=None):
    """
    schemes contains a list of replace this list with the hash(es) you wish
    to support.
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
    :param passwordmanager_schemes, list of schemes for default
            passwordmanager to use
    :return:
    """
    models = ModelProxy()
    for cls2 in args:
        models[cls2.__name__] = cls2

    model_service_mapping = import_model_service_mappings()

    for cls in args:
        if cls.__name__ == 'User':
            if kwargs.get('passwordmanager'):
                cls.passwordmanager = kwargs['passwordmanager']
            else:
                cls.passwordmanager = make_passwordmanager(
                    kwargs.get('passwordmanager_schemes'))

        for cls2 in args:
            setattr(models, cls2.__name__, cls2)

        setattr(cls, "_ziggurat_models", models)
        # if model has a manager attached attached the class also to manager
        services = model_service_mapping.get(cls.__name__, [])
        for service in services:
            setattr(service, 'model', cls)
            setattr(service, 'models_proxy', models)
