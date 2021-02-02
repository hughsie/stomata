Stomata
=======

A simple IPFS gateway re-implementing some of the Pinata API.

This is probably not a good idea to use in production.

Setting up the web service
--------------------------

You can set up the development database manually using:

    $ sudo su - postgres
    $ psql
    > CREATE USER stomata WITH PASSWORD 'stomata' CREATEDB;
    > CREATE DATABASE stomata OWNER stomata;
    > quit

Remember to edit `/var/lib/pgsql/data/pg_hba.conf` and add the `md5` auth
method for localhost.

Then create the schema using:

    FLASK_APP=stomata.py ./env/bin/flask initdb
    FLASK_APP=stomata.py ./env/bin/flask db stamp
    FLASK_APP=stomata.py ./env/bin/flask db upgrade
