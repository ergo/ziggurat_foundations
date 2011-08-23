from setuptools import setup
import sys
setup(name='pyramid_reactor',
      version='0.1',
      description=""" Set of classes that are reusable across various types of
      apps, base user object, auth relationships + structured resource tree
      """,
      author='Marcin Lulek',
      author_email='info@webreactor.eu',
      license='BSD',
      packages=['pyramid_reactor'],
      test_suite='pyramid_reactor.tests',
      install_requires=["sqlalchemy", "cryptacular", 'pyramid','webhelpers']
      )
