#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,too-many-branches

""" Toy client for testing Stomata """

import os
import sys
import argparse

from urllib.parse import urljoin
import requests


def _client_run(args, argv):

    if len(argv) == 0:
        sys.exit(1)

    if argv[0] == "ls":
        r = requests.get(
            urljoin(args.host, "data/pinList"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
        )
    elif argv[0] == "rm":
        try:
            ipfs_hash = argv[1]
        except IndexError as _:
            print("Argument required: IPFS_HASH")
            return
        r = requests.delete(
            urljoin(args.host, "pinning/unpin/{}".format(ipfs_hash)),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
        )
    elif argv[0] == "add":
        try:
            ipfs_hash = argv[1]
        except IndexError as _:
            print("Argument required: IPFS_HASH")
            return
        r = requests.post(
            urljoin(args.host, "pinning/pinByHash"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
            json={
                "hashToPin": ipfs_hash,
                "pinataMetadata": {
                    "name": "firmware.cab",
                    "keyvalues": {"vendor_id": 128},
                },
            },
        )
    elif argv[0] == "md":
        try:
            ipfs_hash = argv[1]
        except IndexError as _:
            print("Argument required: IPFS_HASH")
            return
        r = requests.put(
            urljoin(args.host, "pinning/hashMetadata"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
            json={
                "ipfsPinHash": ipfs_hash,
                "name": "firmware.cab",
                "keyvalues": {"vendor_id": 129},
            },
        )
    elif argv[0] == "pub":
        try:
            ipfs_hash = argv[1]
        except IndexError as _:
            print("Argument required: IPFS_HASH")
            return
        r = requests.post(
            urljoin(args.host, "publishing/publishByHash"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
            json={"hashToPublish": ipfs_hash},
        )
    elif argv[0] == "file":
        try:
            filename = argv[1]
        except IndexError as _:
            print("Argument required: FILENAME")
            return
        files = {
            "file": (
                filename,
                open(filename, "rb"),
                "application/vnd.ms-cab-compressed",
                {
                    "name": filename,
                    "keyvalues": {
                        "FirmwareId": 12345,
                        "bannedCountryCodes": ["SY", "GB"],
                    },
                },
            )
        }
        r = requests.post(
            urljoin(args.host, "pinning/pinFileToIPFS"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
            },
            files=files,
        )
    else:
        print("unknown command")
        sys.exit(1)

    print(r.text)
    print("status code", r.status_code)


if __name__ == "__main__":

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--host",
        default=os.environ.get("HOST", "http://127.0.0.1:5000"),
        help="Server URI",
    )
    parser.add_argument(
        "--api-key",
        default=os.environ.get("API_KEY", "Foo"),
        help="Service API key",
    )
    parser.add_argument(
        "--secret-api-key",
        default=os.environ.get("SECRET_API_KEY", "Bar"),
        help="Service secret API key",
    )
    _args, _argv = parser.parse_known_args()
    _client_run(_args, _argv)
