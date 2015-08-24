========
Tutorial
========

Installation and initial migration
==================================

Install the package::

    pip install ziggurat_foundations

Now it's time to initialize your model structure with alembic.

You will first need to install alembic version **0.3.4** or above::

    pip install alembic\>=0.3.4

After you obtain recent alembic you can now run your migrations against database of your choice.

.. warning ::
    It is *critical* that you use alembic for migrations, if you perform normal 
    table creation like metadata.create_all() with sqlalchemy you will not be 
    able to perform migrations if database schema changes for ziggurat and some 
    constraints *will* be missing from your database even if things will appear 
    to work fine for you.

First you will need to create alembic.ini file with following contents::

    [alembic]
    script_location = ziggurat_foundations:migrations
    sqlalchemy.url = driver://user:pass@host/dbname
    
    [loggers]
    keys = root,sqlalchemy,alembic
    
    [handlers]
    keys = console
    
    [formatters]
    keys = generic
    
    [logger_root]
    level = WARN
    handlers = console
    qualname =
    
    [logger_sqlalchemy]
    level = WARN
    handlers =
    qualname = sqlalchemy.engine
    
    [logger_alembic]
    level = INFO
    handlers =
    qualname = alembic
    
    [handler_console]
    class = StreamHandler
    args = (sys.stderr,)
    level = NOTSET
    formatter = generic
    
    [formatter_generic]
    format = %(levelname)-5.5s [%(name)s] %(message)s
    datefmt = %H:%M:%S

then you can run migration command::

    alembic upgrade head
    
At this point all your database structure should be prepared for usage.

Using ziggurat_foundations within your application
==================================================

.. warning ::
    class names like User inside ziggurat_foundations.models namespace CAN NOT be changed 
    because they are reused in various queries - unless you reimplement ziggurat_model_init

We need to *include ALL mixins inside our application* 
and map classes together so internal methods can function properly.

How to use the mixins inside your application::

    ... your DBSession and base gets created in your favourite framework ...

    import ziggurat_foundations.models
    from ziggurat_foundations.models.base import BaseModel
    from ziggurat_foundations.models.external_identity import ExternalIdentityMixin
    from ziggurat_foundations.models.group import GroupMixin
    from ziggurat_foundations.models.group_permission import GroupPermissionMixin
    from ziggurat_foundations.models.group_resource_permission import GroupResourcePermissionMixin
    from ziggurat_foundations.models.resource import ResourceMixin
    from ziggurat_foundations.models.user import UserMixin
    from ziggurat_foundations.models.user_group import UserGroupMixin
    from ziggurat_foundations.models.user_permission import UserPermissionMixin
    from ziggurat_foundations.models.user_resource_permission import UserResourcePermissionMixin
    from ziggurat_foundations import ziggurat_model_init
    
    # this is needed for pylons 1.0 / akhet approach to db session
    ziggurat_foundations.models.DBSession = DBSession 
    # optional for folks who pass request.db to model methods

    # Base is sqlalchemy's Base = declarative_base() from your project     
    class Group(GroupMixin, Base):
    pass
    
    class GroupPermission(GroupPermissionMixin, Base):
        pass
    
    class UserGroup(UserGroupMixin, Base):
        pass
    
    class GroupResourcePermission(GroupResourcePermissionMixin, Base):
        pass
    
    class Resource(ResourceMixin, Base):
        ... your own properties....
        pass
    
    class UserPermission(UserPermissionMixin, Base):
        pass
    
    class UserResourcePermission(UserResourcePermissionMixin, Base):
        pass
    
    class User(UserMixin, Base):
        ... your own properties....
        pass

    class ExternalIdentity(ExternalIdentityMixin, Base):
        pass
    
    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource,
                   ExternalIdentity, passwordmanager=None)
                   
.. hint ::
    Because some systems can't utilize bcypt password manager you can pass your own
    cryptacular compatible password manager to ziggurat_model_init, it will be used  
    instead of creating default one.
    
Usage examples
==============

Adding new user
---------------
::

    new_user = User()
    DBSession.add(new_user)
    ... populating new row ... 
    new_user.regenerate_security_code()
    new_user.status = 1
    new_user.set_password(new_password)
    

Adding a resource that the user will own
----------------------------------------
::

    resource = SomeResouce()
    DBSession.add(resource)
    user.resources.append(resource)

Adding arbitrary user a 'view' permission to resource
-----------------------------------------------------
::

    permission = UserResourcePermission(perm_name=perm_name,
                                        user_id=user.user_id)
    resource.user_permissions.append(permission)


Checking permissions for users
------------------------------

Checking "resourceless" permission like "user can access admin panel::

    request.user.permissions
    for perm_user, perm_name in request.user.permissions:
        print perm_user, perm_name

Checking all permissions user has to specific resource::

    resource = Resource.by_resource_id(rid)
    for perm in resource.perms_for_user(user):
        print perm.user, perm.perm_name, perm.type, perm.group, perm.resource, perm.owner
        .... list acls ....

Fetch all resources that user can "edit" or "vote"::

    user.resources_with_perms(["edit","vote"])

Connecting external identity like twitter login
-----------------------------------------------
::

    ex_identity = ExternalIdentity()
    ex_identity.external_id = XXX 
    ex_identity.external_user_name = XXX
    ex_identity.provider_name = 'twitter.com'
    ex_identity.access_token = XXX
    ex_identity.token_secret = XXX
    new_user.external_identities.append(ex_identity)


Pyramid based examples of permission system building
====================================================

Example root context factory for pyramid to provide customizable permissions for specific views
-----------------------------------------------------------------------------------------------

This root factory can be used to allow only authenticated users to view::

    class RootFactory(object):
        def __init__(self, request):
            self.__acl__ = [(Allow, Authenticated, u'view'), ]
            # general page factory - append custom non resource permissions
            # request.user object from cookbook recipie
            if request.user:
                for perm in request.user.permissions:
                    self.__acl__.append((Allow, perm.user.user_name, perm.perm_name,))

This example covers the case where every view is secured with a default "view" permission, 
and some pages require other permissions like "view_admin_panel", "create_objects" etc.
Those permissions are appended dynamicly if authenticated user is present, and has additional
custom permissions.

Example resource based pyramid context factory that can be used with url dispatch
---------------------------------------------------------------------------------

This example shows how to protect and authorize users to perform actions on 
resources, you can configure your view to expect "edit" or "delete" permissions:: 

    class ResourceFactory(object):
        def __init__(self, request):
            self.__acl__ = []
            rid = request.matchdict.get("resource_id")
    
            if not rid:
                raise HTTPNotFound()
            self.resource = Resource.by_resource_id(rid)
            if not self.resource:
                raise HTTPNotFound()
            if self.resource and request.user:
                # append basic resource acl that gives all permissions to owner
                self.__acl__ = self.resource.__acl__
                # append permissions that current user may have for this context resource
                for perm in self.resource.perms_for_user(request.user):
                    self.__acl__.append((Allow, perm.user.user_name, perm.perm_name,))