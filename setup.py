from setuptools import setup, find_packages
import sys


found_packages = find_packages()
found_packages.append('ziggurat_foundations.migrations.versions')

setup(name='ziggurat_foundations',
      version='0.4',
      description=""" Set of classes that are reusable across various types of
      web apps, base user object, auth relationships + structured resource tree
      """,
      author='Marcin Lulek',
      author_email='info@webreactor.eu',
      license='BSD',
      packages=found_packages,
      zip_safe=True,
      include_package_data=True,
      package_data={
        '': ['*.txt', '*.rst', '*.ini'],
        },
      test_suite='ziggurat_foundations.tests',
      install_requires=["sqlalchemy", "cryptacular", "paginate",
        "paginate_sqlalchemy", "alembic", "six"]
      )