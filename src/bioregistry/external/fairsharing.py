# -*- coding: utf-8 -*-

"""Scraper for FAIRsharing.

.. seealso:: https://beta.fairsharing.org/API_doc
"""

import json
from typing import Any, Iterable, Mapping, Optional

import pystow
import requests
from tqdm import tqdm

from bioregistry.data import EXTERNAL

__all__ = [
    "get_fairsharing",
]

DIRECTORY = EXTERNAL / "fairsharing"
DIRECTORY.mkdir(exist_ok=True, parents=True)
RAW_PATH = DIRECTORY / "raw.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "https://api.fairsharing.org"
SIGNIN_URL = f"{BASE_URL}/users/sign_in"
RECORDS_URL = f"{BASE_URL}/fairsharing_records"


def get_fairsharing(force_download: bool = False):
    """Get the FAIRsharing registry."""
    # if PROCESSED_PATH.exists() and not force_download:
    #     with PROCESSED_PATH.open() as file:
    #         return json.load(file)

    client = FairsharingClient()
    # As of 2021-12-13, there are a bit less than 4k records that take about 3 minutes to download
    rv = list(
        tqdm(client.iter_records(), unit_scale=True, unit="record", desc="Downloading FAIRsharing")
    )
    with RAW_PATH.open("w") as file:
        json.dump(rv, file, indent=2, ensure_ascii=False)

    # TODO processing

    #with PROCESSED_PATH.open("w") as file:
    #    json.dump(rv, file, indent=2, sort_keys=True)
    return rv


Record = Mapping[str, Any]


class FairsharingClient:
    """A client for programmatic access to the FAIRsharing private API."""

    def __init__(self, user: Optional[str] = None, password: Optional[str] = None):
        """Instantiate the client and get an appropriate JWT token.

        :param user: FAIRsharing username
        :param password: Corresponding FAIRsharing password
        """
        self.username = pystow.get_config(
            "fairsharing", "login", passthrough=user, raise_on_missing=True
        )
        self.password = pystow.get_config(
            "fairsharing", "password", passthrough=password, raise_on_missing=True
        )
        self.jwt = self.get_jwt()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.jwt}",
            }
        )

    def get_jwt(self) -> str:
        """Get the JWT."""
        payload = {
            "user": {
                "login": self.username,
                "password": self.password,
            },
        }
        res = requests.post(SIGNIN_URL, json=payload).json()
        return res["jwt"]

    def iter_records(self) -> Iterable[Record]:
        """Iterate over all FAIRsharing records."""
        yield from self._iter_records_helper(RECORDS_URL)

    def _preprocess_record(self, record):
        if "type" in record:
            del record["type"]
        record = {"id": record["id"], **record["attributes"]}

        for key in [
            "created-at",
            "domains",  # maybe use later
            "legacy-ids" "fairsharing-licence",  # redundant across all records
            "licence-links",
            "publications",
            "taxonomies",
            "updated-at",
            "url-for-logo",
            "user-defined-tags",
        ]:
            if key in record:
                del record[key]
        return record

    def _iter_records_helper(self, url: str) -> Iterable[Record]:
        res = self.session.get(url).json()
        for record in res["data"]:
            yv = self._preprocess_record(record)
            if yv:
                yield yv

        next_url = res["links"].get("next")
        if next_url:
            yield from self._iter_records_helper(next_url)


if __name__ == "__main__":
    get_fairsharing(force_download=True)
