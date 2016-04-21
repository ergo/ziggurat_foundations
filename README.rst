|Build Status| |Coverage Status| |PyPI|

Ziggurat Foundations
=====================

.. image:: https://badges.gitter.im/ergo/ziggurat_foundations.svg
   :alt: Join the chat at https://gitter.im/ergo/ziggurat_foundations
   :target: https://gitter.im/ergo/ziggurat_foundations?utm_source=badge&utm_medium=badge&utm_campaign=pr-badge&utm_content=badge

**DOCUMENTATION**: http://readthedocs.org/docs/ziggurat-foundations/en/latest/

**BUG TRACKER**: https://github.com/ergo/ziggurat_foundations

Top layer to make authentication, resource ownership and permission management
fast, simple and easy. In summary, Ziggurat Foundations (Zigg), is a set of framework agnostic 
set of sqlalchemy classes, but most of the documentation refers to using it
within pyramid. It is the perfect solution for handling complex login and user
management systems, from e-commerce systems, to private intranets or large (and small)
CMS systems.  It can easily be extended to support any additional features you may need (explained
further in the documentation)

Zigg has been used (at scale) for very large implementations (millions of real users) and
has been extended for custom applications such as geo-location applications that rely
on pin-point accuracy for a users location. Zigg has been designed to work for
high end environments, where the user(s) are at the main focus of the application 
(for example Zigg could become the backbone for a social media style application).

Zigg supplies a set of *sqlalchemy mixins* that can be used to extend
models in your application built in pyramid/flask/(your-favourite-framework-here).
The aim of this project is to supply set of generic models that cover the most
common needs in application development when it comes to authorization - using
flat and tree like data structures. We provide nearly every feature you will need in
a standard application, but provide the mixins as we understand that every implementation
has its own use case and in doing so, extending the base models is very easy.


Zigg supplies extendable, robust and well tested models that include:

- User - base for user accounts
- Group - container for many users
- Resource - Arbitrary database entity that can represent various object hierarchies - blogs, forums, cms documents, pages etc.

Zigg provides standard functions that let you:

- Assign arbitrary permissions directly to users (ie. access certain views)
- Assign users to groups
- Assign arbitrary permissions to groups
- Assign arbitrary resource permissions to users (ie. only user X can access private forum)
- Assign arbitrary resource permissions to groups
- Assign a user o an external identity (such as facebook/twitter)
- Manage the sign in/sign out process
- Change users password and generate security codes
- Example root factory for assiginging permissions per request


Ziggurat Foundations is BSD Licensed

.. |Build Status| image:: https://travis-ci.org/ergo/ziggurat_foundations.svg?branch=master
   :target: https://travis-ci.org/ergo/ziggurat_foundations
.. |Coverage Status| image:: https://coveralls.io/repos/ergo/ziggurat_foundations/badge.png?branch=master
   :target: https://coveralls.io/r/ergo/ziggurat_foundations?branch=master
.. |PyPI| image:: http://img.shields.io/pypi/dm/ziggurat_foundations.svg
   :target: https://pypi.python.org/pypi/ziggurat_foundations/
