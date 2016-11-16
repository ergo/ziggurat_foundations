Usage examples
==============

Basics
------

Create a user called "Joe"

.. code-block:: python

    new_user = User(user_name="joe")
    DBSession.add(new_user)
    # At this point new_user becomes a User object, which contains special
    # functions that we will describe in this documentation.

Now we have the user Joe, we can generate a security code for the user (useful for sending
email validation links). Whilst we are doing this, we can assign him a password

.. code-block:: python

    new_user.set_password("secretpassword")
    new_user.regenerate_security_code()

Now we have a user, lets create a group to store users in, lets say Joe is an admin user
and so we will create a group called "admins" and add Joe to this group:

.. code-block:: python

    new_group = Group(group_name="admins")
    DBSession.add(new_group)
    # Now new_group becomes a Group object we can access
    group_entry = UserGroup(group_id=new_group.id, user_id=new_user.id)
    DBSession.add(group_entry)

So now we have the user Joe as part of the group "admins", but this on its
own does nothing, we now want to let give all members of the admin group
permission to access a certain view, for example the view below would
only be accessible to users (and groups) who had the permission "delete":

.. code-block:: python

    @view_config(route_name='delete_users',
        renderer='templates/delete_users.jinja2',
        permission='delete')
    def delete_users(request):
        # do some stuff
        return

So we can do this one of two ways, we can either add the "delete" permission
directly to the user, or assign the delete permission to a group (that the user
is part of)

.. code-block:: python

    # assign the permission to a group
    new_group_permission = GroupPermission(perm_name="delete", group_id=new_group.id)
    DBSession.add(new_group_permission)
    # or assign the permssion directly to a user
    new_user_permission = UserPermission(perm_name="delete", user_id=new_user.id)
    DBSession.add(new_user_permission)

Now we move on to resource permissions, adding a resource that the user will own

.. code-block:: python

    resource = SomeResouce()
    DBSession.add(resource)
    # Assuming "user" is a User() object
    user.resources.append(resource)

Here we show a demo fo how to add a custom "read" permission for user "foo" for a given resource:

.. code-block:: python

    permission = UserResourcePermission()
    permission.perm_name = "read"
    permission.user_name = "foo"
    resource.user_permissions.append(permission)

We can now fetch all resources with permissions "edit", "vote":

.. code-block:: python

    # assuming "user" is a User() object as described as above
    user.resources_with_perms(["edit","vote"])

If we have a user object, we can fetch all non-resource based permissions for user:

.. code-block:: python

    user.permissions

Given a resource fetching all permissions for user, both direct and
inherited from groups user belongs to:

.. code-block:: python

    resource.perms_for_user(user_instance)

Checking "resourceless" permission like "user can access admin panel:

.. code-block:: python

    request.user.permissions
    for perm_user, perm_name in request.user.permissions:
        print(perm_user, perm_name)

Checking all permissions user has to specific resource:

.. no-code-block:: python

    resource = Resource.by_resource_id(rid)
    for perm in resource.perms_for_user(user):
        print(perm.user, perm.perm_name, perm.type, perm.group, perm.resource, perm.owner)
        .... list acls ....


Here is an example of how to connect a user to an external identity like twitter login:

.. code-block:: python

    ex_identity = ExternalIdentity()
    ex_identity.external_id = XXX
    ex_identity.external_user_name = XXX
    ex_identity.provider_name = 'twitter.com'
    ex_identity.access_token = XXX
    ex_identity.token_secret = XXX
    new_user.external_identities.append(ex_identity)

Tree Structures
---------------

Create a tree structure manager:


.. code-block:: python

    from ziggurat_foundations.models.services.resource_tree import ResourceTreeService
    from ziggurat_foundations.models.services.resource_tree_postgres import \
        ResourceTreeServicePostgreSQL

    TreeService = ResourceTreeService(ResourceTreeServicePostgreSQL)


Create a new resource and place it somewhere:

.. code-block:: python

    resource = Resource(...)

    # this accounts for the newly inserted row so the total_children
    # will be max+1 position for new row
    total_children = tree_service.count_children(
        resource.parent_id, db_session=self.request.dbsession)

    tree_service.set_position(
        resource_id=resource.resource_id, to_position=total_children,
        db_session=self.request.dbsession)


Delete some resource and all its descendants:

.. code-block:: python

    tree_service.delete_branch(resource.resource_id)


Move node to some other location in tree:

.. code-block:: python

    tree_service.move_to_position(
        resource_id=resource.resource_id, new_parent_id=X,
        to_position=Y, db_session=request.dbsession)