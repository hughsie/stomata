#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,too-many-branches,too-many-statements

""" Toy client for testing Stomata """

import os
import sys
import argparse
from typing import Any, List, Dict

from urllib.parse import urljoin
import requests


def _client_run(args: Any, argv: List[str]) -> None:

    if args.command == "ls":
        r = requests.get(
            urljoin(args.host, "data/pinList"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
        )
    elif args.command == "rm":
        try:
            ipfs_hash = argv[0]
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
    elif args.command == "add":
        try:
            ipfs_hash = argv[0]
        except IndexError as _:
            print("Argument required: IPFS_HASH [NAME] [KEY] [VALUE]")
            return
        md: Dict[str, Any] = {}
        try:
            md["name"] = argv[1]
            md["keyvalues"] = {argv[2]: argv[3]}
        except IndexError as _:
            pass
        r = requests.post(
            urljoin(args.host, "pinning/pinByHash"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
            json={
                "hashToPin": ipfs_hash,
                "pinataMetadata": md,
            },
        )
    elif args.command == "md":
        md = {}
        try:
            ipfs_hash = argv[0]
            key = argv[1]
        except IndexError as _:
            print("Argument required: IPFS_HASH KEY [VALUE]")
            return
        try:
            md[key] = argv[2]
        except IndexError as _:
            md[key] = None
        print(md)
        r = requests.put(
            urljoin(args.host, "pinning/hashMetadata"),
            headers={
                "pinata_api_key": args.api_key,
                "pinata_secret_api_key": args.secret_api_key,
                "Content-Type": "application/json",
            },
            json={
                "ipfsPinHash": ipfs_hash,
                "keyvalues": md,
            },
        )
    elif args.command == "name":
        try:
            ipfs_hash = argv[0]
            name = argv[1]
        except IndexError as _:
            print("Argument required: IPFS_HASH NAME")
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
                "name": name,
            },
        )
    elif args.command == "pub":
        try:
            ipfs_hash = argv[0]
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
    elif args.command == "file":
        try:
            filename = argv[0]
        except IndexError as _:
            print("Argument required: FILENAME [KEY VALUE]")
            return
        md = {}
        try:
            if argv[1] == "bannedCountryCodes":
                md["keyvalues"] = {argv[1]: argv[2].split(",")}
            else:
                md["keyvalues"] = {argv[1]: argv[2]}
        except IndexError as _:
            pass
        files = {
            "file": (
                filename,
                open(filename, "rb"),
                "application/vnd.ms-cab-compressed",
                {
                    "name": filename,
                    "keyvalues": md,
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
    parser.add_argument(
        "command",
        choices=["ls", "name", "rm", "pin", "add", "md", "ls", "pub", "file"],
        help="Command to run",
    )
    _args, _argv = parser.parse_known_args()
    _client_run(_args, _argv)
