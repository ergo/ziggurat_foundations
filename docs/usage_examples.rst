Using Ziggurat Foundations
==========================

Overview
--------

Ziggurat Foundations supplies a set of *sqlalchemy mixins* that can be used to extend
Zigguart's base models, within your application. The aim of this project is to supply set of generic
models that cover the most common needs in application development when it comes
to authorization, user management, permission management and resource management,
using flat and tree like data structures. Ziggurat is stable and well tested, meaning
it can plug straight in to your application and dramatically reduce development time,
as you can concentrate on your application code.

Ziggurat supplies extendable, robust and well tested models that include:

- User - base for user accounts
- Group - container for many users
- Resource - Arbitrary database entity that can represent various object hierarchies - blogs, forums, cms documents, pages etc.


Ziggurat provides standard functions that let you:

- Assign arbitrary permissions directly to users (ie. access certain views)
- Assign users to groups
- Assign arbitrary permissions to groups
- Assign arbitrary resource permissions to users (ie. only user X can access private forum)
- Assign arbitrary resource permissions to groups
- Assign a user o an external identity (such as facebook/twitter)
- Manage the sign in/sign out process
- Change users password and generate security codes
- Example root factory for assiginging permissions per request


Functions that we supply between those patterns allow for complex and flexible permission
systems that are easly understandable for non-technical users, whilst at the same time
providing a stable base for systems coping with millions of users.

Due to the fact that we supply all models as mixins, the base of Ziggurat can be very easily
extended, for example if you wanted to extend the user model to include a column such as
"customer_number", you can simply do the following:

.. code-block:: python

    class User(UserMixin, Base):
        customer_number = Column(Integer)

.. warning::
   Be cautious about creating your database models directly without the use of alembic.
   we provide alembic migrations for all models supplied (and will continue to do so for future
   releases). This ensures a smooth and documented upgrade of the database design, that can be
   rolled back at any time.

Usage examples
--------------

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
    new_group_permission = GroupPermission(perm_name="delete", group_id=group.id)
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
