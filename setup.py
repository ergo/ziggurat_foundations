from setuptools import setup
import sys
setup(name='ziggurat_foundations',
      version='0.1',
      description=""" Set of classes that are reusable across various types of
      pyramid apps, base user object, auth relationships + structured resource tree
      """,
      author='Marcin Lulek',
      author_email='info@webreactor.eu',
      license='BSD',
      packages=['ziggurat_foundations'],
      test_suite='ziggurat_foundations.tests',
      install_requires=["sqlalchemy", "cryptacular", 'pyramid','webhelpers']
      )