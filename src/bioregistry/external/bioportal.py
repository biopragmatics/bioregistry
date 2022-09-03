# -*- coding: utf-8 -*-

"""Download the NCBO BioPortal registry.

Get an API key by logging up, signing in, and navigating to https://bioportal.bioontology.org/account.
"""

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pystow
import requests
from tqdm.contrib.concurrent import thread_map

from bioregistry.constants import EXTERNAL

__all__ = [
    "get_bioportal",
    "get_agroportal",
    "get_ecoportal",
]

BIOPORTAL_BASE_URL = "https://data.bioontology.org"
ECOPORTAL_BASE_URL = "http://ecoportal.lifewatch.eu:8080"
AGROPORTAL_BASE_URL = "http://data.agroportal.lirmm.fr"


@dataclass
class OntoPortalClient:
    """A client for an OntoPortal site, like BioPortal."""

    metaprefix: str
    base_url: str
    api_key: Optional[str] = None
    directory: Path = field(init=False)
    raw_path: Path = field(init=False)
    processed_path: Path = field(init=False)

    def __post_init__(self):
        self.directory = EXTERNAL.joinpath(self.metaprefix)
        self.directory.mkdir(exist_ok=True, parents=True)
        self.raw_path = self.directory.joinpath("raw.json")
        self.processed_path = self.directory.joinpath("processed.json")

    def query(self, url: str, **params) -> requests.Response:
        """Query the given endpoint on the OntoPortal site.

        :param url: URL to query
        :param params: Kwargs to give as params to :func:`requests.get`
        :returns: The response from :func:`requests.get`

        The rate limit is 15 queries per second. See:
        https://www.bioontology.org/wiki/Annotator_Optimizing_and_Troublehooting
        """
        if self.api_key is None:
            self.api_key = pystow.get_config(self.metaprefix, "api_key", raise_on_missing=True)
        params.setdefault("apikey", self.api_key)
        return requests.get(url, params=params)

    def download(self, force_download: bool = False):
        """Get the full dump of the OntoPortal site's registry."""
        if self.processed_path.exists() and not force_download:
            with self.processed_path.open() as file:
                return json.load(file)

        # see https://data.bioontology.org/documentation#Ontology
        res = self.query(self.base_url + "/ontologies", summaryOnly=False, notes=True)
        records = res.json()
        # Pop the context, which is non-deterministically returend by the API
        for record in records:
            record.pop("@context", None)
        with self.raw_path.open("w") as file:
            json.dump(records, file, indent=2, sort_keys=True)

        records = thread_map(self.process, records, disable=True)
        rv = {result["prefix"]: result for result in records}

        with self.processed_path.open("w") as file:
            json.dump(rv, file, indent=2, sort_keys=True)
        return rv

    def process(self, entry):
        """Process a record from the OntoPortal site's API."""
        prefix = entry["acronym"]
        extra_data = {}
        # res = query(f'{BASE_URL}/ontologies/{bioportal_key}/latest_submission')
        # if res:
        #     extra_data = res.json()
        # else:
        #     print('failed on', bioportal_key)
        #     extra_data = {}

        contact = (extra_data.get("contact") or [{}])[0]
        rv = {
            "prefix": prefix,
            "name": entry["name"],
            "description": extra_data.get("description"),
            "contact": contact.get("email"),
            "contact.label": contact.get("name"),
            "homepage": extra_data.get("homepage"),
            "version": extra_data.get("version"),
            "publication": extra_data.get("publication"),
        }
        return {k: v for k, v in rv.items() if v is not None}


bioportal_client = OntoPortalClient(
    metaprefix="bioportal",
    base_url=BIOPORTAL_BASE_URL,
)


def get_bioportal(force_download: bool = False):
    """Get the BioPortal registry."""
    return bioportal_client.download(force_download=force_download)


ecoportal_client = OntoPortalClient(
    metaprefix="ecoportal",
    base_url=ECOPORTAL_BASE_URL,
)


def get_ecoportal(force_download: bool = False):
    """Get the EcoPortal registry."""
    return ecoportal_client.download(force_download=force_download)


agroportal_client = OntoPortalClient(
    metaprefix="agroportal",
    base_url=AGROPORTAL_BASE_URL,
)


def get_agroportal(force_download: bool = False):
    """Get the AgroPortal registry."""
    return agroportal_client.download(force_download=force_download)


if __name__ == "__main__":
    print("AgroPortal has", len(get_agroportal(force_download=True)))  # noqa:T201
    print("EcoPortal has", len(get_ecoportal(force_download=True)))  # noqa:T201
    print("BioPortal has", len(get_bioportal(force_download=True)))  # noqa:T201
