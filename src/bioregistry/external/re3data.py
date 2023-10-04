# -*- coding: utf-8 -*-

"""Re3data is a registry of research data repositories.

Example API endpoint: https://www.re3data.org/api/v1/repository/r3d100010772
"""

import json
import logging
from typing import Any, Mapping, Optional, Tuple
from xml.etree import ElementTree

import requests
from tqdm.contrib.concurrent import thread_map
from tqdm.contrib.logging import logging_redirect_tqdm

from bioregistry.constants import EXTERNAL
from bioregistry.utils import removeprefix

__all__ = [
    "get_re3data",
]

logger = logging.getLogger(__name__)
DIRECTORY = EXTERNAL / "re3data"
DIRECTORY.mkdir(exist_ok=True, parents=True)
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "https://www.re3data.org"
SCHEMA = "{http://www.re3data.org/schema/2-2}"


def get_re3data(force_download: bool = False):
    """Get the re3data registry.

    This takes about 9 minutes since it has to look up each of the ~3K
    records with their own API call.

    :param force_download: If true, re-downloads the data
    :returns: The re3data pre-processed data
    """
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    res = requests.get(f"{BASE_URL}/api/v1/repositories")
    tree = ElementTree.fromstring(res.text)

    identifier_to_doi = {}
    for repository in tree.findall("repository"):
        identifier_element = repository.find("id")
        if identifier_element is None or identifier_element.text is None:
            continue

        doi_element = repository.find("doi")
        doi = (
            removeprefix(doi_element.text, "https://doi.org/")
            if doi_element and doi_element.text
            else None
        )
        identifier_to_doi[identifier_element.text.strip()] = doi

    records = dict(
        thread_map(
            _get_record,
            identifier_to_doi,
            unit_scale=True,
            unit="record",
            desc="Getting re3data",
            disable=True,
        )
    )

    # backfill DOIs
    for identifier, record in records.items():
        doi = identifier_to_doi.get(identifier)
        if doi:
            record["doi"] = doi

    with PROCESSED_PATH.open("w") as file:
        json.dump(records, file, indent=2, sort_keys=True, ensure_ascii=False)

    return records


def _get_record(identifier: str) -> Tuple[str, Mapping[str, Any]]:
    res = requests.get(f"{BASE_URL}/api/v1/repository/{identifier}")
    tree = ElementTree.fromstring(res.text)[0]
    return identifier, _process_record(identifier, tree)


def _process_record(identifier: str, tree_inner):
    xrefs = (
        _clean_xref(element.text.strip())
        for element in tree_inner.findall(f"{SCHEMA}repositoryIdentifier")
    )
    data = {
        "prefix": identifier,
        "name": tree_inner.find(f"{SCHEMA}repositoryName").text,
        "description": tree_inner.find(f"{SCHEMA}description").text,
        "homepage": tree_inner.find(f"{SCHEMA}repositoryURL").text,
        "synonyms": [
            element.text.strip() for element in tree_inner.findall(f"{SCHEMA}additionalName")
        ],
        "xrefs": dict(tup for tup in xrefs if tup),
    }

    license_element = tree_inner.find(f"{SCHEMA}databaseLicense/{SCHEMA}databaseLicenseName")
    if license_element:
        data["license"] = license_element.text

    return {k: v.strip() if isinstance(v, str) else v for k, v in data.items() if v}


def _clean_xref(xref: str) -> Optional[Tuple[str, str]]:
    if (
        xref.startswith("FAIRsharing_DOI:10.25504/")
        or xref.startswith("FAIRsharing_doi:10.25504/")
        or xref.startswith("FAIRsharing_dOI:10.25504/")
        or xref.startswith("FAIRSharing_doi:10.25504/")
        or xref.startswith("FAIRsharing_doi;10.25504/")
        or xref.startswith("FAIRsharing_doi: 10.25504/")
        or xref.startswith("fairsharing_DOI:10.25504/")
        or xref.startswith("fairsharing_doi:10.25504/")
        or xref.startswith("FAIRsharin_doi:10.25504/")
        or xref.startswith("FAIRsharing_doi.:10.25504/")
        or xref.startswith("FAIRsharing_DOI: 10.25504/")
        or xref.startswith("FAIRsharing_doi::10.25504/")
        or xref.startswith("FAIRsharing_doi:10.24404/")
    ):
        return "fairsharing", xref[len("FAIRsharing_DOI:10.25504/") :]

    for start, key in [
        ("biodbcore-", "biodbcore"),
        ("MIR:", "miriam"),
        ("ROR:", "ror"),
        ("OMICS_", "omics"),
        ("Omics_", "omics"),
        ("omics_", "omics"),
        ("ISSN ", "issn"),
        ("ISSN: ", "issn"),
        ("nif-", "nif"),
        ("ISNI:", "isni"),
        ("doi.org/", "doi"),
        ("doi:", "doi"),
        ("DOI:", "doi"),
        ("DOI: ", "doi"),
        ("RID:nlx_", "nlx"),
        ("PSSB-", "pssb"),
        ("OpenDOAR:", "opendoar"),
        ("openDOAR:", "opendoar"),
        ("ROAR:", "roar"),  # e.g., see http://roar.eprints.org/14208/
        ("hdl:", "hdl"),
        ("https://fairsharing.org/", "fairsharing.legacy"),
        ("http://fairsharing.org/", "fairsharing.legacy"),
        ("Wikidata:", "wikidata"),
        ("https://doi.org/10.5281/zenodo.", "zenodo"),
        ("https://doi.org/", "doi"),
    ]:
        if xref.startswith(start):
            return key, xref[len(start) :]

    if xref.startswith("RRID:"):
        inner_xref = xref[len("RRID:") :]
        if "_" in inner_xref:
            prefix, identifier = inner_xref.split("_", 1)
            return prefix.lower(), identifier
        elif "-" in inner_xref:
            try:
                prefix, identifier = inner_xref.split("-", 1)
            except ValueError:
                logger.debug("can't parse RRID: %s", xref)
            else:
                return prefix.lower(), identifier
        else:
            logger.debug("unknown RRID: %s", xref)
            return None

    if "doi:" in xref:
        for part in xref.split(" "):
            if part.startswith("doi"):
                return "doi", part[len("doi:") :]

    logger.debug("re3data record had unparsable xref: %s", xref)
    return None


if __name__ == "__main__":
    with logging_redirect_tqdm():
        get_re3data(force_download=True)
