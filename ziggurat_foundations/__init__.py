# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import pkg_resources

from ziggurat_foundations.utils import ModelProxy, noop  # noqa

__version__ = pkg_resources.get_distribution("ziggurat_foundations").parsed_version


def import_model_service_mappings():
    from ziggurat_foundations.models.services.user import UserService
    from ziggurat_foundations.models.services.group import GroupService
    from ziggurat_foundations.models.services.group_permission import (
        GroupPermissionService,
    )
    from ziggurat_foundations.models.services.user_permission import (
        UserPermissionService,
    )
    from ziggurat_foundations.models.services.user_resource_permission import (
        UserResourcePermissionService,
    )
    from ziggurat_foundations.models.services.group_resource_permission import (
        GroupResourcePermissionService,
    )  # noqa
    from ziggurat_foundations.models.services.resource import ResourceService
    from ziggurat_foundations.models.services.resource_tree import ResourceTreeService
    from ziggurat_foundations.models.services.external_identity import (
        ExternalIdentityService,
    )

    return {
        "User": [UserService],
        "Group": [GroupService],
        "GroupPermission": [GroupPermissionService],
        "UserPermission": [UserPermissionService],
        "UserResourcePermission": [UserResourcePermissionService],
        "GroupResourcePermission": [GroupResourcePermissionService],
        "Resource": [ResourceService, ResourceTreeService],
        "ExternalIdentity": [ExternalIdentityService],
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
    pwd_context = CryptContext(schemes=schemes, deprecated="auto")
    return pwd_context


def ziggurat_model_init(
    user=None,
    group=None,
    user_group=None,
    group_permission=None,
    user_permission=None,
    user_resource_permission=None,
    group_resource_permission=None,
    resource=None,
    external_identity=None,
    *args,
    **kwargs
):
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
    models.User = user
    models.Group = group
    models.UserGroup = user_group
    models.GroupPermission = group_permission
    models.UserPermission = user_permission
    models.UserResourcePermission = user_resource_permission
    models.GroupResourcePermission = group_resource_permission
    models.Resource = resource
    models.ExternalIdentity = external_identity

    model_service_mapping = import_model_service_mappings()

    if kwargs.get("passwordmanager"):
        user.passwordmanager = kwargs["passwordmanager"]
    else:
        user.passwordmanager = make_passwordmanager(
            kwargs.get("passwordmanager_schemes")
        )

    for name, cls in models.items():
        # if model has a manager attached attached the class also to manager
        services = model_service_mapping.get(name, [])
        for service in services:
            setattr(service, "model", cls)
            setattr(service, "models_proxy", models)
