"""Re3data is a registry of research data repositories.

Example API endpoint: https://www.re3data.org/api/v1/repository/r3d100010772
"""

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar, Optional
from xml.etree import ElementTree

import requests
from tqdm.contrib.concurrent import thread_map

from bioregistry.external.alignment_utils import Aligner, load_processed
from bioregistry.utils import removeprefix

__all__ = [
    "Re3dataAligner",
    "get_re3data",
]

logger = logging.getLogger(__name__)
DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"

BASE_URL = "https://www.re3data.org"
SCHEMA = "{http://www.re3data.org/schema/2-2}"


def get_re3data(force_download: bool = False) -> dict[str, dict[str, Any]]:
    """Get the re3data registry.

    This takes about 9 minutes since it has to look up each of the ~3K records with
    their own API call.

    :param force_download: If true, re-downloads the data

    :returns: The re3data pre-processed data
    """
    if PROCESSED_PATH.exists() and not force_download:
        return load_processed(PROCESSED_PATH)

    res = requests.get(f"{BASE_URL}/api/v1/repositories", timeout=15)
    tree = ElementTree.fromstring(res.text)

    identifier_to_doi = {}
    for repository in tree.findall("repository"):
        identifier_element = repository.find("id")
        if identifier_element is None or identifier_element.text is None:
            continue

        doi_element = repository.find("doi")
        doi = (
            removeprefix(doi_element.text, "https://doi.org/")
            if doi_element is not None and doi_element.text
            else None
        )
        identifier_to_doi[identifier_element.text.strip()] = doi

    records = dict(
        thread_map(  # type:ignore
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


def _get_record(identifier: str) -> tuple[str, Mapping[str, Any]]:
    res = requests.get(f"{BASE_URL}/api/v1/repository/{identifier}", timeout=15)
    tree = ElementTree.fromstring(res.text)[0]
    return identifier, _process_record(identifier, tree)


def _process_record(identifier: str, tree_inner: ElementTree.Element) -> dict[str, Any]:
    xrefs = (
        _clean_xref(element.text.strip())
        for element in tree_inner.findall(f"{SCHEMA}repositoryIdentifier")
        if element.text is not None
    )
    data = {
        "prefix": identifier,
        "name": tree_inner.findtext(f"{SCHEMA}repositoryName"),
        "description": tree_inner.findtext(f"{SCHEMA}description"),
        "homepage": tree_inner.findtext(f"{SCHEMA}repositoryURL"),
        "synonyms": [
            element.text.strip()
            for element in tree_inner.findall(f"{SCHEMA}additionalName")
            if element.text is not None
        ],
        "xrefs": dict(tup for tup in xrefs if tup),
    }

    license_element = tree_inner.find(f"{SCHEMA}databaseLicense/{SCHEMA}databaseLicenseName")
    if license_element is not None:
        data["license"] = license_element.text

    return {k: v.strip() if isinstance(v, str) else v for k, v in data.items() if v}


def _clean_xref(xref: str) -> Optional[tuple[str, str]]:
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


class Re3dataAligner(Aligner):
    """Aligner for the Registry of Research Data Repositoris (r3data)."""

    key = "re3data"
    alt_key_match = "name"
    getter = get_re3data
    curation_header: ClassVar[Sequence[str]] = ("name", "homepage", "description")


if __name__ == "__main__":
    Re3dataAligner.cli()
