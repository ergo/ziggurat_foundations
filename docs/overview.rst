Overview of functionality
=========================

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
- Resource trees management

Ziggurat provides standard functions that let you:

- Assign arbitrary permissions directly to users (ie. access certain views)
- Assign users to groups
- Assign arbitrary permissions to groups
- Assign arbitrary resource permissions to users (ie. only user X can access private forum)
- Assign arbitrary resource permissions to groups
- Manage nested resources with tree service
- Assign a user o an external identity (such as facebook/twitter)
- Change users password and generate security codes
- Manage the sign in/sign out process (pyramid extension)
- Example root factory for assiginging permissions per request (for pyramid)


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

   **NEVER** create your ziggurat database models directly without the use of alembic.
   we provide alembic migrations for all models supplied (and will continue to do so for future
   releases). This ensures a smooth and documented upgrade of the database design.
