# -*- coding: utf-8 -*-

"""Scraper for FAIRsharing.

.. seealso:: https://beta.fairsharing.org/API_doc
"""

import json
from typing import Any, Iterable, Mapping, MutableMapping, Optional

import pystow
import requests
from tqdm import tqdm

from bioregistry.constants import EXTERNAL
from bioregistry.utils import removeprefix

__all__ = [
    "get_fairsharing",
]

DIRECTORY = EXTERNAL / "fairsharing"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "https://api.fairsharing.org"
SIGNIN_URL = f"{BASE_URL}/users/sign_in"
RECORDS_URL = f"{BASE_URL}/fairsharing_records"


ALLOWED_TYPES = {
    "terminology_artefact",
    # "knowledgebase",
    # "knowledgebase_and_repository",
    # "repository",
}


def get_fairsharing(force_download: bool = False, use_tqdm: bool = False):
    """Get the FAIRsharing registry."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    client = FairsharingClient()
    # As of 2021-12-13, there are a bit less than 4k records that take about 3 minutes to download
    rv = {
        row.pop("prefix"): row
        for row in tqdm(
            client.iter_records(),
            unit_scale=True,
            unit="record",
            desc="Downloading FAIRsharing",
            disable=not use_tqdm,
        )
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, ensure_ascii=False, sort_keys=True)

    return rv


KEEP = {
    "abbreviation",
    "description",
    "id",
    "name",
    "prefix",
    "subjects",
    "publications",
}


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

    def iter_records(self) -> Iterable[Mapping[str, Any]]:
        """Iterate over all FAIRsharing records."""
        yield from self._iter_records_helper(RECORDS_URL)

    def _preprocess_record(
        self, record: MutableMapping[str, Any]
    ) -> Optional[MutableMapping[str, Any]]:
        if "type" in record:
            del record["type"]
        record = {"id": record["id"], **record["attributes"]}
        if record.get("record_type") not in ALLOWED_TYPES:
            return None

        doi = record.get("doi")
        if doi is None:
            # tqdm.write(f"{record['id']} has no DOI: {record['url']}")
            # these records are not possible to resolve
            return None
        if doi.startswith("10.25504/"):
            record["prefix"] = record.pop("doi")[len("10.25504/") :]
        else:
            tqdm.write(f"DOI has unexpected prefix: {record['doi']}")

        record["description"] = removeprefix(
            record.get("description"), "This FAIRsharing record describes: "
        )
        record["name"] = removeprefix(record.get("name"), "FAIRsharing record for: ")
        record["publications"] = [
            {k: publication[k] for k in ("doi", "pubmed_id", "title")}
            for publication in record.get("publications", [])
            if publication.get("doi") or publication.get("pubmed_id")
        ]
        # for key in [
        #     "created-at",
        #     "domains",  # maybe use later
        #     "legacy-ids",
        #     "fairsharing-licence",  # redundant across all records
        #     "licence-links",
        #     "taxonomies",
        #     "updated-at",
        #     "url-for-logo",
        #     "user-defined-tags",
        #     "countries",
        #     "fairsharing-registry",
        #     "record-type",
        #     "url",  # redundant of doi
        # ]
        return {key: value for key, value in record.items() if key in KEEP}

    def _iter_records_helper(self, url: str) -> Iterable[Mapping[str, Any]]:
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
