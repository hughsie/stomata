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

Set up the IPFS daemon with:

    wget https://dist.ipfs.io/go-ipfs/v0.7.0/go-ipfs_v0.7.0_linux-amd64.tar.gz
    tar -xvzf go-ipfs_v0.7.0_linux-amd64.tar.gz
    export IPFS_PATH=/mnt/ipfs
    ./go-ipfs/ipfs init --profile server
    ./go-ipfs/ipfs daemon &

You can test this locally using:

    HOST="http://127.0.0.1:5000" API_KEY="Foo" SECRET_API_KEY="Bar" ./env/bin/python ./stomata/client.py ls
