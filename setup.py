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
    license='BSD',
    classifiers=[
        'Classifier: Development Status :: 5 - Production/Stable',
        'Classifier: Framework :: Flask',
        'Classifier: Framework :: Pylons',
        'Classifier: Framework :: Pyramid',
        'Classifier: License :: OSI Approved :: BSD License',
        'Classifier: Programming Language :: Python :: 2.7',
        'Classifier: Programming Language :: Python :: 3.3',
        'Classifier: Programming Language :: Python :: 3.4',
        'Classifier: Programming Language :: Python :: 3.5'
    ],
    packages=find_packages(),
    zip_safe=True,
    include_package_data=True,
    package_data={
        '': ['*.txt', '*.rst', '*.ini', '*.mako'],
        'ziggurat_foundations': ['migrations/versions/*.py'],
    },
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
