from setuptools import setup, find_packages
from ziggurat_foundations import __version__

version = '{}.{}.{}'.format(__version__['major'],
                            __version__['minor'],
                            __version__['patch'])

setup(
    name='ziggurat_foundations',
    version=version,
    description=""" Set of classes that are reusable across various types of
    web apps, base user object, auth relationships + structured resource tree
    """,
    author='Marcin Lulek',
    author_email='info@webreactor.eu',
    license='BSD',
    packages=find_packages(),
    zip_safe=True,
    # include_package_data=True,
    package_data={
        '': ['*.txt', '*.rst', '*.ini', '*.mako', 'README'],
        'ziggurat_foundations': ['migrations/versions/*.py'],
    },
    test_suite='ziggurat_foundations.tests',
    tests_require=[
        "coverage"
    ],
    install_requires=[
        "sqlalchemy",
        "passlib>=1.6.1",
        "paginate",
        "paginate_sqlalchemy",
        "alembic",
        "six"]
)
