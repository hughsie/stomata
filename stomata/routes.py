#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,singleton-comparison,no-member,cyclic-import

""" JSON and HTML routes """

import json

import os
from typing import Any, Dict
from functools import wraps

import ipfshttpclient

from flask import request, render_template
from sqlalchemy.orm.exc import NoResultFound

from stomata import app, db
from .models import Ipfs, IpfsAttr


def api_key_required(f):  # type: ignore
    """ requires authentication header """

    @wraps(f)
    def decorated_function(*args, **kwargs):  # type: ignore
        """ checks the API keys """
        try:
            if request.headers.get("Pinata-Api-Key") != app.config["STOMATA_API_KEY"]:
                return {
                    "error": {
                        "reason": "INVALID_API_KEYS",
                        "details": "Invalid API key provided",
                    }
                }, 401
            if (
                request.headers.get("Pinata-Secret-Api-Key")
                != app.config["STOMATA_SECRET_API_KEY"]
            ):
                return {
                    "error": {
                        "reason": "INVALID_API_KEYS",
                        "details": "Invalid secret API key provided",
                    }
                }, 401
        except KeyError as e:
            return {"error": str(e)}, 500

        # success
        return f(*args, **kwargs)

    return decorated_function


@app.route("/", methods=["GET"])
def index() -> Any:
    """ the index page """
    return render_template("index.html")


@app.route("/users/generateApiKey", methods=["POST"])
@api_key_required
def generate_api_key() -> Any:
    """ FIXME: generate an API key """
    return {}, 404


@app.route("/users/revokeApiKey", methods=["PUT"])
@api_key_required
def revoke_api_key() -> Any:
    """ FIXME: revoke an API key """
    return {}, 404


@app.route("/pinning/hashMetadata", methods=["PUT"])
@api_key_required
def hash_metadata() -> Any:
    """ set metadata on an existing Ipfs object """

    # get ipfs hash
    try:
        payload = json.loads(request.data.decode("utf8"))
        ipfs_hash = payload["ipfsPinHash"]
    except KeyError as e:
        return {"error": str(e)}, 500

    # find in database
    try:
        ipfs = db.session.query(Ipfs).filter(Ipfs.pin_hash == ipfs_hash).one()
    except NoResultFound as e:
        return {"error": str(e)}, 500

    if "name" in payload:
        ipfs.name = payload["name"]
    keyvalues = payload.get("keyvalues", {})
    for key in keyvalues:
        attr = ipfs.attr(key)
        if attr:
            if keyvalues[key] == None:
                ipfs.attrs.remove(attr)
                continue
            attr.value = keyvalues[key]
            continue
        ipfs.attrs.append(IpfsAttr(key=key, value=keyvalues[key]))
    db.session.commit()

    # success
    return "OK", 200


@app.route("/hashPinPolicy", methods=["PUT"])
@api_key_required
def hash_pin_policy() -> Any:
    """ FIXME: set pin policy """
    return {}, 404


def _add_to_db(ipfs_hash, md) -> None:
    """ add an added IPFS hash to the database """
    ipfs = Ipfs(pin_hash=ipfs_hash)
    if md:
        ipfs.name = os.path.basename(md.get("name"))
        ipfs.size = md.get("size", 0)
        keyvalues = md.get("keyvalues", {})
        for key in keyvalues:
            ipfs.attrs.append(IpfsAttr(key=key, value=str(keyvalues[key])))
    db.session.add(ipfs)
    db.session.commit()


@app.route("/pinning/pinByHash", methods=["POST"])
@api_key_required
def pin_by_hash() -> Any:
    """ pin an existing upload to IPFS """

    # get ipfs hash
    try:
        payload = json.loads(request.data.decode("utf8"))
        ipfs_hash = payload["hashToPin"]
    except KeyError as e:
        return {"error": str(e)}, 500

    # find in database
    ipfs = db.session.query(Ipfs).filter(Ipfs.pin_hash == ipfs_hash).first()
    if ipfs:
        return {"error": "Already pinned"}, 400

    # proxy
    try:
        with ipfshttpclient.connect() as client:
            client.pin.add(ipfs_hash)
    except KeyError as e:
        return {"error": str(e)}, 500

    # add to database
    md = payload.get("pinataMetadata")
    _add_to_db(ipfs_hash, md)

    # success -- yes: this is a different case to pinFileToIPFS...
    return {
        "id": ipfs.ipfs_id,
        "ipfsHash": ipfs_hash,
        "status": "searching",
        "name": ipfs.name,
    }


@app.route("/pinning/pinFileToIPFS", methods=["POST"])
@api_key_required
def pin_file_to_ipfs() -> Any:
    """Upload a new file and pin it to the IPFS.

    There is one special Stomata-specific ``keyvalues`` value of
    ``bannedCountryCodes`` that is used to ensure the export control setting
    for the file matches that set on the server.

    If the server does not prevent downloads from a country set from the
    metadata then an error is returned and the file is not added or pinned.
    """

    # get uploaded fileitem
    try:
        fileitem = request.files["file"]
    except KeyError as e:
        return {"error": str(e)}, 500

    # get metadata early to check banned country codes
    keyvalues = {}
    try:
        keyvalues = json.loads(fileitem.headers["keyvalues"].replace("'", '"'))
    except KeyError as _:
        pass
    try:
        for country_code in keyvalues["bannedCountryCodes"]:
            if country_code not in app.config["BANNED_COUNTRY_CODES"]:
                return {
                    "Error": "country code {} is not included in server "
                    "BANNED_COUNTRY_CODES=[{}]".format(
                        country_code, ",".join(app.config["BANNED_COUNTRY_CODES"])
                    )
                }, 400
    except KeyError as _:
        pass

    # proxy
    blob = fileitem.read()
    try:
        with ipfshttpclient.connect() as client:
            ipfs_hash = client.add_bytes(blob)
    except ipfshttpclient.exceptions.ErrorResponse as e:
        return {"error": str(e)}, 500

    # find in database
    ipfs = db.session.query(Ipfs).filter(Ipfs.pin_hash == ipfs_hash).first()
    if ipfs:
        return {
            "IpfsHash": ipfs_hash,
            "PinSize": ipfs.size,
            "Name": ipfs.name,
            "Timestamp": ipfs.date_pinned.isoformat(),
        }

    # actually pin this time
    try:
        with ipfshttpclient.connect() as client:
            client.pin.add(ipfs_hash)
    except ipfshttpclient.exceptions.ErrorResponse as e:
        return {"error": str(e)}, 500

    # add to database
    md = {}
    md["name"] = fileitem.filename
    md["size"] = len(blob)
    md["keyvalues"] = keyvalues
    try:
        md["name"] = fileitem.headers["name"]
    except KeyError as _:
        pass
    _add_to_db(ipfs_hash, md)

    # success -- yes: this is a different case to pinByHash...
    return {
        "IpfsHash": ipfs_hash,
        "PinSize": ipfs.size,
        "Timestamp": ipfs.date_pinned.isoformat(),
    }


@app.route("/pinJobs", methods=["GET"])
@api_key_required
def pin_jobs() -> Any:
    """ FIXME: return pending jobs """
    return {}, 404


@app.route("/pinning/pinJSONToIPFS", methods=["POST"])
@api_key_required
def pin_json_to_ipfs() -> Any:
    """ FIXME: pin a JSON blob to the IPFS """

    # {
    #    pinataMetadata: {
    #        name: 'ItemStatus'
    #        keyvalues: {
    #            ItemID: 'Item001',
    #        }
    #    },
    #    pinataContent: {
    #        inspectedBy: 'Inspector001',
    #    }
    # }

    return {}, 404


@app.route("/pinning/unpin/<ipfs_hash>", methods=["DELETE"])
def unpin(ipfs_hash: str) -> Any:
    """ unpin an object from the IPFS """

    # find in database
    try:
        ipfs = db.session.query(Ipfs).filter(Ipfs.pin_hash == ipfs_hash).one()
    except NoResultFound as _:
        return {"error": "Current user has not pinned hash: {}".format(ipfs_hash)}, 500

    # proxy
    try:
        with ipfshttpclient.connect() as client:
            client.pin.rm(ipfs_hash)
    except ipfshttpclient.exceptions.ErrorResponse as e:
        return {"error": str(e)}, 500

    # success
    db.session.delete(ipfs)
    db.session.commit()
    return "OK", 200


@app.route("/pinning/userPinPolicy", methods=["PUT"])
@api_key_required
def user_pin_policy() -> Any:
    """ set the new pin policy for the user """

    return {}, 404


def _get_metadata(ipfs: Ipfs) -> Dict[str, Any]:
    """ get the metadata JSON for a given Ipfs object """
    keyvalues: Dict[str, Any] = {}
    for attr in ipfs.attrs:
        keyvalues[attr.key] = attr.value
    return {"name": ipfs.name, "keyvalues": keyvalues}


@app.route("/data/pinList", methods=["GET"])
@api_key_required
def pin_list() -> Any:
    """ gets the list of pins for this server """

    # proxy
    try:
        with ipfshttpclient.connect() as client:
            keys = client.pin.ls()["Keys"]
    except KeyError as e:
        return {"error": str(e)}, 500

    rows = []
    for ipfs_hash in keys:
        if keys[ipfs_hash]["Type"] == "indirect":
            continue

        # find in database
        ipfs = db.session.query(Ipfs).filter(Ipfs.pin_hash == ipfs_hash).first()
        if not ipfs:
            continue
        rows.append(
            {
                "id": ipfs.ipfs_id,
                "ipfs_pin_hash": ipfs_hash,
                "size": ipfs.size,
                "user_id": app.config["ADMIN_EMAIL"],
                "date_pinned": ipfs.date_pinned.isoformat(),
                "date_unpinned": None,
                "metadata": _get_metadata(ipfs),
                "regions": [
                    {
                        "regionId": 0,
                        "desiredReplicationCount": 1,
                        "currentReplicationCount": 1,
                    }
                ],
            }
        )

    return {"count": len(rows), "rows": rows}


@app.route("/publishing/publishByHash", methods=["POST"])
@api_key_required
def publish_by_hash() -> Any:
    """ publish an existing IPFS object using IPNS """

    # get ipfs hash
    try:
        payload = json.loads(request.data.decode("utf8"))
        ipfs_hash = payload["hashToPublish"]
    except KeyError as e:
        return {"error": str(e)}, 500

    # find in database
    try:
        _ = db.session.query(Ipfs).filter(Ipfs.pin_hash == ipfs_hash).one()
    except NoResultFound as e:
        return {"error": str(e)}, 500

    # proxy
    try:
        with ipfshttpclient.connect() as client:
            ipnshash = client.name.publish(ipfs_hash)["Name"]
    except KeyError as e:
        return {"error": str(e)}, 500

    # success
    return {"IpnsHash": ipnshash}
