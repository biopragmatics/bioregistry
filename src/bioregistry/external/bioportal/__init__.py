"""Download the NCBO BioPortal registry.

Get an API key by logging up, signing in, and navigating to
https://bioportal.bioontology.org/account.
"""

import json
import math
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, cast

import ontoportal_client
import pystow
import requests
from ontoportal_client.constants import (
    AGROPORTAL_BASE_URL,
    BIODIVPORTAL_BASE_URL,
    BIOPORTAL_BASE_URL,
    ECOPORTAL_BASE_URL,
)
from tqdm import tqdm
from tqdm.contrib.concurrent import thread_map

from bioregistry.alignment_model import (
    License,
    Publication,
    Record,
    dump_records,
    load_processed,
    make_record,
)
from bioregistry.constants import EMAIL_RE, RAW_DIRECTORY
from bioregistry.external.alignment_utils import adapter
from bioregistry.license_standardizer import standardize_license
from bioregistry.utils import removeprefix

__all__ = [
    "get_agroportal",
    "get_biodivportal",
    "get_bioportal",
    "get_ecoportal",
]

DIRECTORY = Path(__file__).parent.resolve()


@dataclass
class OntoPortalClient:
    """A client for an OntoPortal site, like BioPortal."""

    metaprefix: str
    base_url: str
    api_key: str | None = None
    raw_path: Path = field(init=False)
    processed_path: Path = field(init=False)
    client: ontoportal_client.OntoPortalClient = field(init=False)
    max_workers: int = 2

    def __post_init__(self) -> None:
        self.raw_path = RAW_DIRECTORY.joinpath(self.metaprefix).with_suffix(".json")
        self.processed_path = DIRECTORY.joinpath(self.metaprefix).with_suffix(".json")
        self.api_key = pystow.get_config(
            self.metaprefix, "api_key", passthrough=self.api_key, raise_on_missing=True
        )
        self.client = ontoportal_client.OntoPortalClient(
            base_url=self.base_url, api_key=self.api_key
        )

    def download(
        self, force_download: bool = False, force_process: bool = False
    ) -> dict[str, Record]:
        """Get the full dump of the OntoPortal site's registry."""
        if self.processed_path.exists() and not force_download and not force_process:
            return load_processed(self.processed_path)

        records = self._get_records(force=force_download)

        rv = dict(
            thread_map(  # type:ignore
                self.process, records, disable=True, description=f"Processing {self.metaprefix}"
            )
        )

        dump_records(rv, self.processed_path)
        return rv

    def _get_records(self, force: bool = False) -> list[dict[str, Any]]:
        if self.raw_path.exists() and not force:
            return cast(list[dict[str, Any]], json.loads(self.raw_path.read_text()))

        records = self.client.get_ontologies(summary_only=False, notes=True)
        records = thread_map(
            self._preprocess,
            records,
            unit="ontology",
            max_workers=self.max_workers,
            desc=f"Preprocessing {self.metaprefix}",
        )
        with self.raw_path.open("w") as file:
            json.dump(records, file, indent=2, sort_keys=True, ensure_ascii=False)

        return records

    def _preprocess(self, record: dict[str, Any]) -> dict[str, Any]:
        record.pop("@context", None)
        prefix = record["acronym"]
        try:
            res_json = self.client.get_latest_submission(prefix, display="all")
        except requests.exceptions.HTTPError as e:
            tqdm.write(f"{self.metaprefix}:{prefix} had issue getting submission details: {e}")
            return record

        publications = res_json.get("publication")
        if isinstance(publications, str):
            record["publications"] = [publications]
        elif isinstance(publications, list):
            record["publications"] = publications

        for key in [
            "homepage",
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
            {k: v.strip() for k, v in contact.items() if not k.startswith("@") and v}
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

    def process(self, entry: dict[str, Any]) -> tuple[str, Record]:
        """Process a record from the OntoPortal site's API."""
        prefix = entry["acronym"]
        rv = {
            "name": entry["name"].strip(),
            "description": entry.get("description"),
            "contact": entry.get("contact"),
            "homepage": entry.get("homepage"),
            "version": entry.get("version"),
            "repository": entry.get("repository"),
        }
        if license_name := entry.get("license"):
            rv["license"] = License(name=license_name)
        if publications := entry.pop("publications", None):
            rv["publications"] = _handle_publications(publications)
        if example_uri := entry.get("exampleIdentifier"):
            rv.setdefault("extras", {})["example_uri"] = example_uri

        return prefix, make_record(rv)


def _handle_publications(ll: list[str]) -> list[Publication]:
    # TODO this should get upstreamed somewhere, since it's such a common pattern
    rv = []
    for url in ll:
        if url.startswith("https://doi.org/"):
            rv.append(Publication(doi=url.removeprefix("https://doi.org/")))
        elif url.startswith("http://doi.org/"):
            rv.append(Publication(doi=url.removeprefix("http://doi.org/")))
        elif url.startswith("https://dx.doi.org/"):
            rv.append(Publication(doi=url.removeprefix("https://dx.doi.org/")))
        elif url.startswith("http://www.ncbi.nlm.nih.gov/pubmed/"):
            rv.append(Publication(pubmed=url.removeprefix("http://www.ncbi.nlm.nih.gov/pubmed/")))
        elif url.startswith("https://www.ncbi.nlm.nih.gov/pubmed/"):
            rv.append(Publication(pubmed=url.removeprefix("https://www.ncbi.nlm.nih.gov/pubmed/")))
        elif url.startswith("https://zenodo.org/records/"):
            rv.append(Publication(zenodo=url.removeprefix("https://zenodo.org/records/")))
        elif url.startswith("https://arxiv.org/abs/"):
            rv.append(Publication(arxiv=url.removeprefix("https://arxiv.org/abs/")))
        else:
            # TODO look back for PMC
            # tqdm.write(f'publication URL: {url}')
            rv.append(Publication(url=url))
    return rv


bioportal_client = OntoPortalClient(
    metaprefix="bioportal",
    base_url=BIOPORTAL_BASE_URL,
)


@adapter
def get_bioportal(force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the BioPortal registry."""
    return bioportal_client.download(force_download=force_download, force_process=force_process)


ecoportal_client = OntoPortalClient(
    metaprefix="ecoportal",
    base_url=ECOPORTAL_BASE_URL,
)


@adapter
def get_ecoportal(force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the EcoPortal registry."""
    return ecoportal_client.download(force_download=force_download, force_process=force_process)


agroportal_client = OntoPortalClient(
    metaprefix="agroportal",
    base_url=AGROPORTAL_BASE_URL,
)


@adapter
def get_agroportal(force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the AgroPortal registry."""
    return agroportal_client.download(force_download=force_download, force_process=force_process)


biodivportal_client = OntoPortalClient(
    metaprefix="biodivportal",
    base_url=BIODIVPORTAL_BASE_URL,
)


@adapter
def get_biodivportal(
    force_download: bool = False, force_process: bool = False
) -> dict[str, Record]:
    """Get the BioDivPortal registry."""
    return biodivportal_client.download(force_download=force_download, force_process=force_process)


if __name__ == "__main__":
    print("BioDivPortal has", len(get_biodivportal(force_download=False, force_process=True)))  # noqa:T201
    # print("EcoPortal has", len(get_ecoportal(force_download=False, force_process=True)))
    # print("AgroPortal has", len(get_agroportal(force_download=False, force_process=True)))
    # print("BioPortal has", len(get_bioportal(force_download=False, force_process=True)))
