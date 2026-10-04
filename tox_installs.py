import os
import subprocess

if os.environ.get("BCRYPT"):
    subprocess.check_call(["pip", "install", "bcrypt"])

if os.environ.get("DB") == "postgres":
    # postgresql:// resolves to psycopg2 on SQLAlchemy < 2.1 and to psycopg 3 on 2.1+
    subprocess.check_call(["pip", "install", "psycopg2-binary", "psycopg[binary]"])

sqlalchemy_version = os.environ.get("SQLALCHEMY_VERSION")
if sqlalchemy_version:
    subprocess.check_call(["pip", "install", "sqlalchemy=={}".format(sqlalchemy_version)])

if os.environ.get("DB") == "mysql":
    subprocess.check_call(
        [
            "pip",
            "install",
            "http://cdn.mysql.com/Downloads/Connector-Python/mysql-connector-python-2.0.4.zip#md5=3df394d89300db95163f17c843ef49df",
        ]
    )

if os.environ.get("DB") == "mysql":
    subprocess.check_call(["pip", "install", "mysqlclient"])
