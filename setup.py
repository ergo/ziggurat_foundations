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

test_deps = [
    "coverage",
    "flake8",
    "pylint",
    "pyramid",
    "pytest",
    "pytest-cov",
    "rstcheck"
]

setup(
    name='ziggurat_foundations',
    version=version,
    description=""" Set of SQLAlchemy mixins that make application building an easy task. Provides users, groups, 
    permissions, resource tree handling and authorization solutions for Pyramid and Flask frameworks.
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
    tests_require=test_deps,
    install_requires=[
        "sqlalchemy",
        "passlib>=1.6.1",
        "paginate",
        "paginate_sqlalchemy",
        "alembic",
        'zope.deprecation >= 3.5.0',
        "six"],
    extras_require = {
        'test': test_deps,
    }
)
