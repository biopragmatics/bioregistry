"""Download the NCBO BioPortal registry.

Get an API key by logging up, signing in, and navigating to https://bioportal.bioontology.org/account.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import pystow
import requests
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from bioregistry.constants import EMAIL_RE, RAW_DIRECTORY
from bioregistry.license_standardizer import standardize_license
from bioregistry.utils import removeprefix

__all__ = [
    "get_agroportal",
    "get_bioportal",
    "get_ecoportal",
]

BIOPORTAL_BASE_URL = "https://data.bioontology.org"
ECOPORTAL_BASE_URL = "http://ecoportal.lifewatch.eu:8080"
AGROPORTAL_BASE_URL = "http://data.agroportal.lirmm.fr"
DIRECTORY = Path(__file__).parent.resolve()


@dataclass
class OntoPortalClient:
    """A client for an OntoPortal site, like BioPortal."""

    metaprefix: str
    base_url: str
    api_key: Optional[str] = None
    raw_path: Path = field(init=False)
    processed_path: Path = field(init=False)
    max_workers: int = 2

    def __post_init__(self):
        self.raw_path = RAW_DIRECTORY.joinpath(self.metaprefix).with_suffix(".json")
        self.processed_path = DIRECTORY.joinpath(self.metaprefix).with_suffix(".json")

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
        records = thread_map(
            self._preprocess,
            records,
            unit="ontology",
            max_workers=self.max_workers,
            desc=f"Preprocessing {self.metaprefix}",
        )
        with self.raw_path.open("w") as file:
            json.dump(records, file, indent=2, sort_keys=True, ensure_ascii=False)

        records = thread_map(
            self.process, records, disable=True, description=f"Processing {self.metaprefix}"
        )
        rv = {result["prefix"]: result for result in records}

        with self.processed_path.open("w") as file:
            json.dump(rv, file, indent=2, sort_keys=True, ensure_ascii=False)
        return rv

    def _preprocess(self, record):
        record.pop("@context", None)
        prefix = record["acronym"]
        url = f"{self.base_url}/ontologies/{prefix}/latest_submission"
        res = self.query(url, display="all")
        if res.status_code != 200:
            tqdm.write(
                f"{self.metaprefix}:{prefix} had issue getting submission details: {res.text}"
            )
            return record
        res_json = res.json()
        for key in [
            "homepage",
            "publication",
            "version",
            "description",
            "exampleIdentifier",
            "repository",
        ]:
            value = res_json.get(key)
            if value:
                if isinstance(value, list) and len(value) == 1:
                    value = value[0]
                if isinstance(value, float) and not math.isnan(value):
                    value = str(value)
                if not isinstance(value, str):
                    tqdm.write(f"got non-string value ({type(value)}) for {key}: {value}")
                    continue
                record[key] = (
                    (value or "")
                    .strip()
                    .replace("\r\n", " ")
                    .replace("\r", " ")
                    .strip()
                    .replace("  ", " ")
                    .replace("  ", " ")
                    .replace("  ", " ")
                )

        license_stub = res_json.get("hasLicense")
        if license_stub:
            record["license"] = standardize_license(license_stub)

        contacts = [
            {k: v.strip() for k, v in contact.items() if not k.startswith("@")}
            for contact in res_json.get("contact", [])
        ]
        contacts = [contact for contact in contacts if EMAIL_RE.match(contact.get("email", ""))]
        if contacts:
            contact = contacts[0]
            # TODO consider sorting contacts in a canonical order?
            # contact = min(contacts, key=lambda c: len(c["email"]))
            record["contact"] = {k: v for k, v in contact.items() if k != "id"}
            name = record["contact"].get("name")
            if name:
                record["contact"]["name"] = removeprefix(removeprefix(name, "Dr. "), "Dr ")

        return {k: v for k, v in record.items() if v}

    def process(self, entry):
        """Process a record from the OntoPortal site's API."""
        prefix = entry["acronym"]
        rv = {
            "prefix": prefix,
            "name": entry["name"].strip(),
            "description": entry.get("description"),
            "contact": entry.get("contact"),
            "homepage": entry.get("homepage"),
            "version": entry.get("version"),
            "publication": entry.get("publication"),
            "repository": entry.get("repository"),
            "example_uri": entry.get("exampleIdentifier"),
            "license": entry.get("license"),
        }
        return {k: v for k, v in rv.items() if v}


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
    print("EcoPortal has", len(get_ecoportal(force_download=True)))  # noqa:T201
    print("AgroPortal has", len(get_agroportal(force_download=True)))  # noqa:T201
    print("BioPortal has", len(get_bioportal(force_download=True)))  # noqa:T201
