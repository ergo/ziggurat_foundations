# bw compat
from ziggurat_foundations.permissions import ANY_PERMISSION, ALL_PERMISSIONS, Allow, Deny, PermissionTuple
from ziggurat_foundations.utils import get_db_session

from .external_identity import ExternalIdentityMixin
from .group import GroupMixin
from .group_permission import GroupPermissionMixin
from .group_resource_permission import GroupResourcePermissionMixin
from .resource import ResourceMixin
from .user import UserMixin
from .user_group import UserGroupMixin
from .user_permission import UserPermissionMixin
from .user_resource_permission import UserResourcePermissionMixin


# should hold global scoped session
DBSession = None

def groupfinder(userid, request):
    if userid and hasattr(request, 'user') and request.user:
        groups = ['group:%s' % g.group_name for g in request.user.groups]
        return groups
    return []