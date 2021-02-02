#!/usr/bin/python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2021 Richard Hughes <richard@hughsie.com>
#
# SPDX-License-Identifier: GPL-2.0+
#
# pylint: disable=invalid-name,singleton-comparison,no-member,unsubscriptable-object

""" objects """

import datetime
from typing import Any, List, Optional

from stomata import db


class IpfsAttr(db.Model):
    """ optional attribute on the Ipfs object """

    __tablename__ = "ipfs_attr"

    ipfs_attribute_id = db.Column(db.Integer, primary_key=True)
    ipfs_id = db.Column(
        db.Integer, db.ForeignKey("ipfs.ipfs_id"), nullable=False, index=True
    )
    key: str = db.Column(db.Text, nullable=False)
    value: str = db.Column(db.Text, default=None)

    ipfs = db.relationship("Ipfs", back_populates="attrs")

    def __lt__(self, other: Any) -> bool:
        return self.key < other.key

    def __repr__(self) -> str:
        return "IpfsAttr({}:{})".format(self.key, self.value)


class Ipfs(db.Model):
    """ a pinned IPFS object """

    __tablename__ = "ipfs"

    ipfs_id = db.Column(db.Integer, primary_key=True)
    pin_hash = db.Column(db.String, nullable=False)
    name: str = db.Column(db.String, default=None)
    date_pinned = db.Column(
        db.DateTime, nullable=False, default=datetime.datetime.utcnow
    )
    size: int = db.Column(db.Integer, default=0)
    attrs: List[IpfsAttr] = db.relationship(
        "IpfsAttr",
        back_populates="ipfs",
        lazy="joined",
        cascade="all,delete,delete-orphan",
    )

    def attr(self, key: str) -> Optional[str]:
        """ return the attribute with the key name """
        for attr in self.attrs:
            if attr.key == key:
                return attr
        return None

    def __repr__(self) -> str:
        return "Ipfs({})".format(self.ipfs_id)
