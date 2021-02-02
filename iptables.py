#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,singleton-comparison,no-member,unsubscriptable-object,too-few-public-methods

""" block countries using iptables """

import sys
import gzip
import csv
import math
import subprocess
from collections import defaultdict

from io import StringIO

from stomata import app


class Netblock:
    """ a range of addresses """

    def __init__(self, addr_from, addr_to):
        self.addr_from = addr_from
        self.addr_to = addr_to

    @property
    def subnet(self) -> int:
        """ return the subnet defining the start to the end """
        return int(math.log(self.addr_to - self.addr_from + 1, 2))


def _value_to_ip_addr(val: int) -> str:
    return "{}.{}.{}.{}".format(
        (val >> 24) & 0xFF, (val >> 16) & 0xFF, (val >> 8) & 0xFF, (val >> 0) & 0xFF
    )


if __name__ == "__main__":

    # read the list of netblocks
    with gzip.open("geoipdata.csv.gz", "rb") as f:
        blob = f.read()
    netblocks = defaultdict(list)
    for row in csv.reader(StringIO(blob.decode("utf-8", "ignore"))):
        try:
            country_code = row[4]
            if country_code not in app.config["BANNED_COUNTRY_CODES"]:
                continue
            netblocks[country_code].append(Netblock(int(row[0]), int(row[1])))
        except IndexError as _:
            pass

    # block each IP range
    for country_code in netblocks:
        print("Blocking country code {}".format(country_code))
        for block in netblocks[country_code]:
            argv = [
                "firewall-cmd",
                "--zone=external",
                "--permanent",
                '--add-rich-rule=rule family="ipv4" source address="{}/{}" drop'.format(
                    _value_to_ip_addr(block.addr_from), block.subnet
                ),
            ]
            try:
                subprocess.run(argv, check=True, capture_output=True)
            except subprocess.CalledProcessError as e:
                print(str(e))
                sys.exit(1)
