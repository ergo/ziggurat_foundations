Configure Ziggurat with Pyramid Framework
=========================================

Examples of permission system building
---------------------------------------

Root context factories for pyramid provide customizable permissions for specific views
inside your appplication. It is a good idea to keep the root factory inside your models
file (if following the basic pyramid tutorial). This root factory can be used to allow
only authenticated users to view:

.. code-block:: python

    from ziggurat_foundations.permissions import permission_to_pyramid_acls

    class RootFactory(object):
        def __init__(self, request):
            self.__acl__ = [(Allow, Authenticated, u'view'), ]
            # general page factory - append custom non resource permissions
            # request.user object from cookbook recipie
            if request.user:
                # for most trivial implementation

                # for perm in request.user.permissions:
                #     self.__acl__.append((Allow, perm.user.id, perm.perm_name,))

                # or alternatively a better way that handles both user
                # and group inherited permissions via `permission_to_pyramid_acls`

                for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                        request.user.permissions):
                    self.__acl__.append((outcome, perm_user, perm_name))

This example covers the case where every view is secured with a default "view" permission,
and some pages require other permissions like "view_admin_panel", "create_objects" etc.
Those permissions are appended dynamicly if authenticated user is present, and has additional
custom permissions.

Example resource based pyramid context factory that can be used with url dispatch
---------------------------------------------------------------------------------

This example shows how to protect and authorize users to perform actions on
resources, you can configure your view to expect "edit" or "delete" permissions:

.. code-block:: python

    from ziggurat_foundations.permissions import permission_to_pyramid_acls

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
                permissions = ResourceService.perms_for_user(
                                              self.resource, request.user)
                for outcome, perm_user, perm_name in permission_to_pyramid_acls(
                        permissions):
                    self.__acl__.append((outcome, perm_user, perm_name,))

Ziggurat Foundations can provide some shortcuts that help build pyramid
applications faster.

.. hint::

    This approach will also work properly for all models inheriting
    from `Resource` class.

Automatic user sign in/sign out
-------------------------------

**ziggurat_foundations.ext.pyramid.sign_in**

This extension registers basic views for user authentication using
**AuthTktAuthenticationPolicy**, and can fetch user object and verify it
against supplied password.

**Extension setup**

To enable this extension it needs to be included via pyramid include mechanism
for example in your ini configuration file:

.. code-block:: ini

    pyramid.includes = pyramid_tm
                       ziggurat_foundations.ext.pyramid.sign_in

or by adding the following to your applications __init__.py configurator file
(both methods yield the same result):

.. code-block:: python

    config.include('ziggurat_foundations.ext.pyramid.sign_in')

this will register 2 routes:

* ziggurat.routes.sign_in with pattern */sign_in*
* ziggurat.routes.sign_out with pattern */sign_out*

.. tip::

    those patterns can be configured to match your app route patterns via
    following config keys:

    * ziggurat_foundations.sign_in.sign_in_pattern = /custom_pattern
    * ziggurat_foundations.sign_in.sign_out_pattern = /custom_pattern

In order to use this extension we need to tell the Ziggurat where User model
is located in your application for example in your ini file:

.. code-block:: ini

    ziggurat_foundations.model_locations.User = yourapp.models:User

Additional config options for extensions to include in your ini configuration file:

.. code-block:: ini

    # name of the POST key that will be used to supply user name
    ziggurat_foundations.sign_in.username_key = login

    # name of the POST key that will be used to supply user password
    ziggurat_foundations.sign_in.password_key = password

    # name of the POST key that will be used to provide additional value that can be used to redirect
    # user back to area that required authentication/authorization)
    ziggurat_foundations.sign_in.came_from_key = came_from

    # If you do not use a global DBSession variable, and you bundle DBSession insde the request
    # you need to tell Ziggurat its naming convention, do this by providing a function that
    # returns the correct request variable
    ziggurat_foundations.session_provider_callable = yourapp.model:get_session_callable


If you are using a db_session inside the request, you need to provide a basic function
to tell Ziggurat where DBSession is inside the request, you can add the following to your
models file (yourapp.model):

.. code-block:: python

    def get_session_callable(request):
        # if DBSession is located at "request.db_session"
        return request.db_session
        # or if DBSession was located at "request.db"
        # return request.db

**Configuring your application views**

Here would be a working form/template used for user authentication and to send
info to one of the new views registered by extension (sign_in), you can put
this code inside any template, as the action is posted directly to pre-registered
Ziggurat views/contexts:

.. code-block:: html+jinja

    <form action="{{request.route_url('ziggurat.routes.sign_in')}}" method="post">
        <!-- "came_from", "password" and "login" can all be overwritten -->
        <input type="hidden" value="OPTIONAL" name="came_from" id="came_from">
        <!-- in the example above we changed the value of "login" to "username" -->
        <input type="text" value="" name="login" <!-- change to name="username" if required --> >
        <input type="password" value="" name="password">
        <input type="submit" value="Sign In" name="submit" id="submit">
    </form>

In next step it is required to register 3 views that will listen for specific
context objects that the extension can return upon form sign_in/sign_out requests:

* **ZigguratSignInSuccess** - user and password were matched
    * contains headers that set cookie to persist user identity,
      fetched user object, "came from" value
* **ZigguratSignInBadAuth** - there were no positive matches for user and password
    * contains headers used to unauthenticate any current user identity
* **ZigguratSignOut** - user signed out of application
    * contains headers used to unauthenticate any current user identity


**Required imports for all 3 views**

So inside the file you will be using for your Ziggurat views, we need to perform
some base imports:

.. code-block:: python

    from pyramid.security import NO_PERMISSION_REQUIRED
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInSuccess
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInBadAuth
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignOut


**ZigguratSignInSuccess context view example**

Now we can provide a fuction, based off of the ZigguratSignInSuccess context

.. code-block:: python

    @view_config(context=ZigguratSignInSuccess, permission=NO_PERMISSION_REQUIRED)
    def sign_in(request):
        # get the user
        user = request.context.user
        # actions performed on sucessful logon, flash message/new csrf token
        # user status validation etc.
        if request.context.came_from != '/':
            return HTTPFound(location=request.context.came_from,
                             headers=request.context.headers)
        else:
            return HTTPFound(location=request.route_url('some_route'),
                             headers=request.context.headers)

**ZigguratSignInBadAuth context view example**

The view below would deal with handling a failed login

.. code-block:: python

    @view_config(context=ZigguratSignInBadAuth, permission=NO_PERMISSION_REQUIRED)
    def bad_auth(request):
        # The user is here if they have failed login, this example
        # would return the user back to "/" (site root)
        return HTTPFound(location=request.route_url('/'),
                         headers=request.context.headers)
        # This view would return the user back to a custom view
        return HTTPFound(location=request.route_url('declined_view'),
                     headers=request.context.headers)


**ZigguratSignOut context view example**

This is a basic view that performs X task once the user has navigated to
"/sign_out" (if using the default location provided by Ziggurat), like the view
above it can be overwritten/modified to do what ever else you would like.

.. code-block:: python

    @view_config(context=ZigguratSignOut, permission=NO_PERMISSION_REQUIRED)
    def sign_out(request):
        return HTTPFound(location=request.route_url('/'),
                         headers=request.context.headers)


Cofiguring groupfinder and session factories
--------------------------------------------

Now before we can actually use the login system, we need to import and include
the groupfinder and session factory inside our application configuration, first
off in our ini file we need to add a session secret:

.. code-block:: ini

    # replace "sUpersecret" with  a secure secret
    session.secret = sUpersecret

Now, we need to configure the groupdiner and authn and authz policy inside the
main __init__.py file of our application, like so:

.. code-block:: python

    from ziggurat_foundations.models import groupfinder

    def main(global_config, **settings):

        # Set the session secret as per out ini file
        session_factory = SignedCookieSessionFactory(
            settings['session.secret'],
        )

        authn_policy = AuthTktAuthenticationPolicy(settings['session.secret'],
            callback=groupfinder)
        authz_policy = ACLAuthorizationPolicy()

        # Tie it all together
        config = Configurator(settings=settings,
                  root_factory='yourapp.models.RootFactory',
                              authentication_policy=authn_policy,
                              authorization_policy=authz_policy)


Modify request to return Ziggurat User() Object
-----------------------------------------------

We provide a method to modify the pyramid request and return a Ziggurat User()
object (if present) in each request. E.g. once a user is logged in, their details
are held in the request (in the form of a userid), if we enable the below function,
we can easily access all user attributes in our code, to include this feature,
enable it by adding the following to your applications __init__.py configurator file:

.. code-block:: python

    config.include('ziggurat_foundations.ext.pyramid.get_user')

Or in your ini configuration file (both methods yield the same result):

.. code-block:: ini

    pyramid.includes = pyramid_tm
                       ziggurat_foundations.ext.pyramid.get_user

Then inside each pyramid view that contains a request, you can access user information
with (the code behind this is as described in the offical pyramid cookbook, but
we include in within Ziggurat to make your life easier):

.. code-block:: python

    @view_config(route_name='edit_note', renderer='templates/edit_note.jinja2',
        permission='edit')
    def edit_note(request):
        user = request.user
        # user is now a Ziggurat/SQLAlchemy object that you can access
        # Example for user Joe
        print (user.user_name)
        "Joe"

.. tip::

    Congratulations, your application is now fully configured to use Ziggurat
    Foundations, take a look at the Usage Examples for a guide (next page) on how to start taking
    advantage of all the features that Ziggurat has to offer!
