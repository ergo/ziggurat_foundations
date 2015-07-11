import hashlib
import random
import string
import six
import sqlalchemy as sa


from ziggurat_foundations.permissions import (ANY_PERMISSION,
                                              ALL_PERMISSIONS,
                                              PermissionTuple,
                                              resource_permissions_for_users)

from ziggurat_foundations.models import get_db_session


class ModelManager(object):
    pass
