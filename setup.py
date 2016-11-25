import os

from setuptools import setup, find_packages

from ziggurat_foundations import __version__

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, 'README.rst')) as f:
    README = f.read()
with open(os.path.join(here, 'CHANGES.rst')) as f:
    CHANGES = f.read()

version = '{}.{}.{}'.format(__version__['major'],
                            __version__['minor'],
                            __version__['patch'])

setup(
    name='ziggurat_foundations',
    version=version,
    description=""" Set of classes that are reusable across various types of
    web apps, base user object, auth relationships + structured resource tree
    """,
    long_description=README,
    author='Marcin Lulek',
    author_email='info@webreactor.eu',
    url='https://github.com/ergo/ziggurat_foundations',
    license='BSD',
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Framework :: Flask',
        'Framework :: Pylons',
        'Framework :: Pyramid',
        'License :: OSI Approved :: BSD License',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3.3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5'
    ],
    packages=find_packages(),
    zip_safe=True,
    include_package_data=True,
    test_suite='ziggurat_foundations.tests',
    tests_require=[
        "coverage",
        "pytest",
        "psycopg2",
        "pytest-cov"
    ],
    install_requires=[
        "sqlalchemy",
        "passlib>=1.6.1",
        "paginate",
        "paginate_sqlalchemy",
        "alembic",
        'zope.deprecation >= 3.5.0',
        "six"]
)
