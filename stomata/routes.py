#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,singleton-comparison,no-member,cyclic-import

""" JSON and HTML routes """

from typing import Any

from flask import render_template

from stomata import app


@app.route("/", methods=["GET"])
def index() -> Any:
    """ the index page """
    return render_template("index.html")
