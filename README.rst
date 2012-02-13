ziggurat_foundations
=====================

Framework agnostic (with slight bias towards pyramid) set of sqlalchemy 
classes that make building applications that require permissions an easy task.

ziggurat_foundations supplies a set of *sqlalchemy mixins* that can be used to extend
models in your application. The aim of this project is to supply set of generic 
models that cover the most common needs in application development when it comes 
to authorization - using flat and tree like data structures.

So far following basics are supplied:

- User - base for user accounts
- Group - container for many users 
- Resource - Arbitrary database entity that can represent various object hierarchies - blogs, forums, cms documents, pages etc.

Currently following information and data manipulation is supported:

- assigning arbitrary permissions directly to users (ie. access admin panel) 
- assigning users to groups
- assigning arbitrary permissions to groups 
- assigning arbitrary resource permissions to users (ie. only user X can access  private forum)
- assigning arbitrary resource permissions to groups 
 
The sqlalchemy mixins make all the interactions easy to use in your application 
and save development time.

Example usage:
--------------

assigning custom "read" permission for user "foo" for a given resource::

    permission = UserResourcePermission()
    permission.perm_name = "read"
    permission.user_name = "foo"
    resource.user_permissions.append(permission)   

fetching all resources with permissions "edit", "vote"::

    user.resources_with_perms(["edit","vote"])

fetching all non-resource based permissions for user::

    user.permissions

given a resource fetching all permissions for user, both direct and  
inherited from groups user belongs to::

    resource.perms_for_user(user_instance)

and a lot more...



How to implement models in your applications:

(class names like User inside ziggurat_foundations.models namespace CAN NOT be changed 
because they are reused in various queries - unless you reimplement ziggurat_model_init)::

    import ziggurat_foundations.models
    from ziggurat_foundations.models import BaseModel, UserMixin, GroupMixin
    from ziggurat_foundations.models import GroupPermissionMixin, UserGroupMixin 
    from ziggurat_foundations.models import GroupResourcePermissionMixin, ResourceMixin 
    from ziggurat_foundations.models import UserPermissionMixin, UserResourcePermissionMixin
    from ziggurat_foundations.models import ExternalIdentityMixin
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
        pass
    
    class UserPermission(UserPermissionMixin, Base):
        pass
    
    class UserResourcePermission(UserResourcePermissionMixin, Base):
        pass
    
    class User(UserMixin, Base):
        pass

    class ExternalIdentity(ExternalIdentityMixin, Base):
        pass
    
    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource,
                   ExternalIdentity, passwordmanager=None)
                   
Because some systems can't utilize bcypt password manager you can pass your own
cryptacular compatible password manager to ziggurat_model_init, it will be used  
instead of creating default one.