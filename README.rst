ziggurat_foundations
=====================

Framework agnostic set of sqlalchemy 
classes that make building applications that require permissions an easy task.

ziggurat_foundations supplies a set of *sqlalchemy mixins* that can be used to extend
models in your application built in pyramid/flask/(your-favourite-framework-here).
The aim of this project is to supply set of generic models that cover the most 
common needs in application development when it comes to authorization - using 
flat and tree like data structures.


**DOCUMENTATION**: http://readthedocs.org/docs/ziggurat-foundations/en/latest/

**BUG TRACKER**: https://github.com/ergo/ziggurat_foundations

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

Ziggurat Foundations is BSD Licensed