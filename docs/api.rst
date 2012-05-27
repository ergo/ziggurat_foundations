=================
API Documentation
=================

  
.. autoclass:: ziggurat_foundations.models.UserMixin
    :members: 
    
    .. attribute:: id

       Unique identifier of user object
   
    .. attribute:: user_name
    
       Unique user name of user object

    .. attribute:: user_password
    
       Password hash for user object
       
    .. attribute:: email
    
       Email for user object

    .. attribute:: status
    
       Status for user object

    .. attribute:: security_code
    
       Security code user object (can be used for password reset etc.
       
    .. attribute:: last_login_date
    
       Date of user's last login
       
    .. attribute:: registered_date
    
       Date of user's registration

    .. attribute:: groups_dynamic
    
       returns dynamic relationship for groups - allowing for filtering of data

    .. attribute:: user_permissions
    
       returns all direct non-resource permissions for this user, allows to assign
       new permissions to user::

            user.user_permissions.append(resource)


    .. attribute:: resource_permissions
    
       returns all direct resource permissions for this use

    .. attribute:: resources
    
       Returns all resources directly owned by user, can be used to assign  
       ownership of new resources::

            user.resources.append(resource)
       
    .. attribute:: external_identities
    
       dynamic relation for external identities for this user - allowing for filtering of data
       
   
.. autoclass:: ziggurat_foundations.models.ExternalIdentityMixin
    :members:
   
   
.. autoclass:: ziggurat_foundations.models.GroupMixin
    :members:
   
   
.. autoclass:: ziggurat_foundations.models.GroupPermissionMixin
    :members:
   
   
.. autoclass:: ziggurat_foundations.models.UserPermissionMixin
    :members:
   
   
.. autoclass:: ziggurat_foundations.models.UserGroupMixin
    :members:
   
   
.. autoclass:: ziggurat_foundations.models.GroupResourcePermissionMixin
    :members:


.. autoclass:: ziggurat_foundations.models.UserResourcePermissionMixin
    :members:
   
   
.. autoclass:: ziggurat_foundations.models.ResourceMixin
    :members:
   
.. autofunction:: ziggurat_foundations.models.get_db_session


.. autoclass:: ziggurat_foundations.models.BaseModel
    :members: