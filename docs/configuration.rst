################################
Configuring Ziggurat Foundations
################################

Installation and initial migration
==================================

Install the package:

.. code-block:: bash

    $ pip install ziggurat_foundations


Now it's time to initialize your model structure with alembic.

You will first need to install alembic:

.. code-block:: bash

    $ pip install alembic>=0.7.0

After you obtain recent alembic you can now run your migrations against
database of your choice.

.. warning::

    It is *critical* that you use alembic for migrations, if you perform normal
    table creation like metadata.create_all() with sqlalchemy you will not be
    able to perform migrations if database schema changes for ziggurat and some
    constraints *will* be missing from your database even if things will appear
    to work fine for you.

First you will need to create alembic.ini file with following contents:

.. code-block:: ini

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

then you can run migration command:

.. code-block:: bash

   $ alembic upgrade head

At this point all your database structure should be prepared for usage.

Implementing ziggurat_foundations within your application
=========================================================

.. warning::

    class names like User inside ziggurat_foundations.models namespace CAN NOT be changed
    because they are reused in various queries - unless you reimplement ziggurat_model_init

We need to *include ALL mixins inside our application*
and map classes together so internal methods can function properly.

In order to use the mixins inside your application, you need to include the follwing code
inside your models file, to extend your existing models (if following the basic pyramid tutorial):

.. code-block:: python

    # ... your DBSession and base gets created in your favourite framework ...

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

    # this is needed for scoped session approach like in pylons 1.0
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
        # ... your own properties....

        # example implementation of ACLS for pyramid application
        @property
        def __acl__(self):
            acls = []

            if self.owner_user_id:
                acls.extend([(Allow, self.owner_user_id, ALL_PERMISSIONS,), ])

            if self.owner_group_id:
                acls.extend([(Allow, "group:%s" % self.owner_group_id,
                              ALL_PERMISSIONS,), ])
            return acls

    class UserPermission(UserPermissionMixin, Base):
        pass

    class UserResourcePermission(UserResourcePermissionMixin, Base):
        pass

    class User(UserMixin, Base):
        # ... your own properties....
        pass

    class ExternalIdentity(ExternalIdentityMixin, Base):
        pass

    # you can define multiple resource derived models to build a complex
    # application like CMS, forum or other permission based solution

    class Entry(Resource):
        """
        Resource of `entry` type
        """

        __tablename__ = 'entries'
        __mapper_args__ = {'polymorphic_identity': 'entry'}

        resource_id = sa.Column(sa.Integer(),
                                sa.ForeignKey('resources.resource_id',
                                              onupdate='CASCADE',
                                              ondelete='CASCADE', ),
                                primary_key=True, )
        # ... your own properties....
        some_property = sa.Column(sa.UnicodeText())


    ziggurat_model_init(User, Group, UserGroup, GroupPermission, UserPermission,
                   UserResourcePermission, GroupResourcePermission, Resource,
                   ExternalIdentity, passwordmanager=None)

.. hint::

    Default password manager will use `pbkdf2_sha256`, but if you want different configuration
    pass passlib compatible password manager to ziggurat_model_init.
