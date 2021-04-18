import os

from setuptools import setup, find_packages

here = os.path.abspath(os.path.dirname(__file__))
with open(os.path.join(here, "README.md")) as f:
    README = f.read()
with open(os.path.join(here, "CHANGES.md")) as f:
    CHANGES = f.read()

test_deps = [
    "coverage",
    "pytest",
    "pytest-cov",
    "tox",
    "mock",
    "pyramid",
    "webtest",
    "pyramid_jinja2",
]

setup(
    name="ziggurat_foundations",
    version="0.8.4",
    description=""" Set of SQLAlchemy mixins that make application building an easy task. Provides users, groups,
    permissions, resource tree handling and authorization solutions for Pyramid and Flask frameworks.
    """,
    long_description_content_type="text/markdown",
    long_description=README,
    author="Marcin Lulek",
    author_email="info@webreactor.eu",
    url="https://github.com/ergo/ziggurat_foundations",
    license="BSD",
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Framework :: Flask",
        "Framework :: Pylons",
        "Framework :: Pyramid",
        "License :: OSI Approved :: BSD License",
        "Programming Language :: Python :: 2",
        "Programming Language :: Python :: 3",
    ],
    packages=find_packages(),
    zip_safe=True,
    include_package_data=True,
    test_suite="ziggurat_foundations.tests",
    tests_require=test_deps,
    install_requires=[
        "sqlalchemy",
        "passlib>=1.6.1",
        "paginate",
        "paginate_sqlalchemy",
        "alembic",
        "zope.deprecation >= 3.5.0",
        "six",
    ],
    setup_requires=["pytest-runner"],
    extras_require={
        "test": test_deps,
        "lint": ["black", "pylint", "rstcheck", "flake8"],
    },
)
