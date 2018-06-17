from __future__ import unicode_literals

# should hold global scoped session
DBSession = None


def groupfinder(userid, request):
    """
    Default groupfinder implementaion for pyramid applications

    :param userid:
    :param request:
    :return:
    """
    if userid and hasattr(request, "user") and request.user:
        groups = ["group:%s" % g.id for g in request.user.groups]
        return groups
    return []
