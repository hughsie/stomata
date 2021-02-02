#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,singleton-comparison,no-member,wrong-import-position

"""
Re-implementation of the Pinata API with support for publishing added.

This is probably not a good idea to use in production.
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)
try:
    app.config.from_pyfile("custom.cfg")
except FileNotFoundError as _:
    app.config.from_pyfile("stomata.cfg")
db: SQLAlchemy = SQLAlchemy(app)

import stomata.routes


@app.cli.command("initdb")
def initdb_command() -> None:
    """ ensure all tables exist """
    db.metadata.create_all(bind=db.engine)


@app.cli.command("dropdb")
def dropdb_command() -> None:
    """ delete all tables: WARNING! """
    db.metadata.drop_all(bind=db.engine)
