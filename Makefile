# Copyright (C) 2019 Richard Hughes <richard@hughsie.com>
# SPDX-License-Identifier: GPL-2.0+

VENV=./env
PYTHON=$(VENV)/bin/python
FLASK=$(VENV)/bin/flask
PIP=$(VENV)/bin/pip

setup: requirements.txt
	virtualenv ./env
	$(VENV)/bin/pip install -r requirements.txt

clean:
	rm -rf ./build

run:
	FLASK_DEBUG=1 FLASK_APP=stomata/__init__.py $(VENV)/bin/flask run
