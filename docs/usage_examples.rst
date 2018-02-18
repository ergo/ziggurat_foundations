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

    UserService.set_password(new_user, "secretpassword")
    UserService.regenerate_security_code(new_user)

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
    UserService.resources_with_perms(user, ["edit","vote"])

If we have a user object, we can fetch all non-resource based permissions for user:

.. code-block:: python

    permissions = UserService.permissions(user)

Given a resource fetching all permissions for user, both direct and
inherited from groups user belongs to:

.. code-block:: python

    ResourceService.perms_for_user(resource, user_instance)

Checking "resourceless" permission like "user can access admin panel:

.. code-block:: python

    permissions = UserService.permissions(request.user)
    for perm_user, perm_name in permissions:
        print(perm_user, perm_name)

Checking all permissions user has to specific resource:

.. no-code-block:: python

    resource = Resource.by_resource_id(rid)
    for perm in ResourceService.perms_for_user(resource, user_instance):
        print(perm.user, perm.perm_name, perm.type, perm.group, perm.resource, perm.owner)
        .... list acls ....

List all **direct** permissions that users have for specific resource

.. no-code-block:: python

    from ziggurat_foundations.permissions import ANY_PERMISSION
    permissions = ResourceService.users_for_perm(
        resource, perm_name=ANY_PERMISSION, skip_group_perms=True)

Here is an example of how to connect a user to an external identity
provider like twitter:

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

.. warning::

    When using `populate_instance` or any other means to set values on resources
    remember to **NOT** modify `ordering` and `parent_id` values on the resource
    rows - always perform tree operations via tree service. Otherwise it will
    confuse the service and it might perform incorrect operations.

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

Fetch all resources that are parent of resource:

.. code-block:: python

    tree_service.path_upper(resource.resource_id, db_session=db_session)

Fetch all children of a resource limiting the amount of levels to go down,
then build a nested dictionary structure out of it:

.. code-block:: python

    result = tree_service.from_resource_deeper(
        resource_id, limit_depth=2, db_session=db_session)
    tree_struct = tree_service.build_subtree_strut(result)

Delete some resource and all its descendants:

.. code-block:: python

    tree_service.delete_branch(resource.resource_id)


Move node to some other location in tree:

.. code-block:: python

    tree_service.move_to_position(
        resource_id=resource.resource_id, new_parent_id=X,
        to_position=Y, db_session=request.dbsession)
