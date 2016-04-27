from __future__ import unicode_literals

# should hold global scoped session
DBSession = None


def groupfinder(userid, request):
    if userid and hasattr(request, 'user') and request.user:
        groups = ['group:%s' % g.id for g in request.user.groups]
        return groups
    return []
