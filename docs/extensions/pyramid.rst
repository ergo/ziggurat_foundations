==================
Pyramid Extensions
==================

ziggurat_foundations can provide some shortcuts that help build pyramid
applications faster.

-------------------------------
Automatic user sign in/sign out
-------------------------------

**ziggurat_foundations.ext.pyramid.sign_in**

This extension registers basic views for user authentication using
**AuthTktAuthenticationPolicy**, and can fetch user object and verify it
against supplied password.

Extension setup
---------------

To enable this extension it needs to be included via pyramid include mechanism
for example:

.. code-block:: ini

    pyramid.includes = pyramid_tm
                       ziggurat_foundations.ext.pyramid.sign_in

or using configurator directives ::

    config.include('ziggurat_foundations.ext.pyramid.sign_in')

this will register 2 routes:

* ziggurat.routes.sign_in with pattern */sign_in*
* ziggurat.routes.sign_out with pattern */sign_out*

.. tip::

    those patterns can be configured to match your app route patterns via
    following config keys:

    * ziggurat_foundations.sign_in.sign_in_pattern = /custom_pattern
    * ziggurat_foundations.sign_in.sign_out_pattern = /custom_pattern

It is also required to tell the extension where User model is located in your
application for example::

    ziggurat_foundations.model_locations.User = yourapp.models:User

Additional config options for extensions include:

* ziggurat_foundations.sign_in.username_key = login *(name of POST key that will
  be used to supply user name )*
* ziggurat_foundations.sign_in.password_key = password *(name of POST key that
  will be used to supply user password)*
* ziggurat_foundations.sign_in.came_from_key = came_from *(name of POST key that
  will be used to provide additional value that can be used to redirect user back
  to area that required authentication/authorization)*

Configuring your application views
-----------------------------------

First you need to make a form used for user authentication and send info to one
of views registered by extension:

.. code-block:: html+jinja

    <form action="{{request.route_url('ziggurat.routes.sign_in')}}" method="post">
        <input type="hidden" value="OPTIONAL" name="came_from" id="came_from">
        <input type="text" value="" name="login">
        <input type="password" value="" name="password">
        <input type="submit" value="Sign In" name="submit" id="submit">
    </form>

In next step it is required to register 3 views that will listen for specific
context objects that extension can return upon form submission/ logout request:

* **ZigguratSignInSuccess** - user and password were matched
    * contains headers that set cookie to persist user identity,
      fetched user object, "came from" value
* **ZigguratSignInBadAuth** - there were no positive matches for user and password
    * contains headers used to unauthenticate any current user identity
* **ZigguratSignOut** - user signed out of application
    * contains headers used to unauthenticate any current user identity


Required imports for all 3 views
................................

::

    from pyramid.security import NO_PERMISSION_REQUIRED
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInSuccess
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignInBadAuth
    from ziggurat_foundations.ext.pyramid.sign_in import ZigguratSignOut


ZigguratSignInSuccess context view example
..........................................

::

    @view_config(context=ZigguratSignInSuccess, permission=NO_PERMISSION_REQUIRED)
    def sign_in(request):
        user = request.context.user
        # actions performed on sucessful logon, flash message/new csrf token
        # user status validation etc.
        if request.context.came_from != '/':
            return HTTPFound(location=request.context.came_from,
                             headers=request.context.headers)
        else:
            return HTTPFound(location=request.route_url('some_route'),
                             headers=request.context.headers)

ZigguratSignInBadAuth context view example
..........................................

::

    @view_config(context=ZigguratSignInBadAuth, permission=NO_PERMISSION_REQUIRED)
    def bad_auth(request):
        # action like a warning flash message on bad logon
        return HTTPFound(location=request.route_url('/'),
                         headers=request.context.headers)


ZigguratSignOut context view example
..........................................

::

    @view_config(context=ZigguratSignOut, permission=NO_PERMISSION_REQUIRED)
    def sign_out(request):
        return HTTPFound(location=request.route_url('/'),
                         headers=request.context.headers)
