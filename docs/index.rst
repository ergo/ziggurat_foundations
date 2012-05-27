.. ziggurat_foundations documentation master file, created by
   sphinx-quickstart on Fri May 25 21:03:39 2012.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to ziggurat_foundations's documentation!
================================================

Framework agnostic (with bias towards pyramid) set of sqlalchemy 
classes that make building applications that require permissions (ACL's) an easy task.

.. tip::

    By default ziggurat aims at **postgresql 8.4+** (CTE support) as main RDBMS system,
    but currently *everything* except recursive queries(for optional resource tree structures) 
    is tested using sqlite, and will run on other popular database systems including mysql.     

**DOCUMENTATION**: http://ziggurat_foundations.readthedocs.org/en/latest/

**BUG TRACKER**: https://bitbucket.org/ergo/ziggurat_foundations

Contents:

.. toctree::
   :maxdepth: 2
   
   overview
   tutorial
   changelog
   api


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

