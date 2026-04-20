"""Re3data is a registry of research data repositories.

Example API endpoint: https://www.re3data.org/api/v1/repository/r3d100010772
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from functools import partial
from pathlib import Path
from typing import Any, ClassVar
from xml.etree import ElementTree

import pystow
from tqdm.contrib.concurrent import thread_map

from bioregistry.alignment_model import License, Record, dump_records, load_processed, make_record
from bioregistry.external.alignment_utils import Aligner, adapter
from bioregistry.utils import removeprefix

__all__ = [
    "Re3dataAligner",
    "get_re3data",
]

logger = logging.getLogger(__name__)
DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"

MODULE = pystow.module("re3data")
RAW_PATH = MODULE.join(name="manifest.xml")

BASE_URL = "https://www.re3data.org"
SCHEMA = "{http://www.re3data.org/schema/2-2}"
MANIFEST_URL = f"{BASE_URL}/api/v1/repositories"


@adapter
def get_re3data(force_download: bool = False, force_process: bool = False) -> dict[str, Record]:
    """Get the re3data registry.

    This takes about 9 minutes since it has to look up each of the ~3K records with
    their own API call.

    :param force_download: If true, re-downloads the data

    :returns: The re3data pre-processed data
    """
    if PROCESSED_PATH.is_file() and not force_download and not force_process:
        return load_processed(PROCESSED_PATH)

    tree = MODULE.ensure_xml(url=MANIFEST_URL, force=force_download, name="manifest.xml")

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

    records: dict[str, Record] = dict(
        thread_map(
            partial(_get_record, force=force_download),
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
            if record.xrefs is None:
                record.xrefs = {}
            record.xrefs["doi"] = doi

    dump_records(records, PROCESSED_PATH)
    return records


def _get_record(identifier: str, force: bool) -> tuple[str, Record]:
    url = f"{BASE_URL}/api/v1/repository/{identifier}"
    tree = MODULE.ensure_xml("records", url=url, force=force, name=f"{identifier}.xml")
    root = tree.getroot()
    return identifier, _process_record(identifier, root[0])


def _process_record(identifier: str, tree_inner: ElementTree.Element) -> Record:
    xrefs = (
        _clean_xref(element.text.strip())
        for element in tree_inner.findall(f"{SCHEMA}repositoryIdentifier")
        if element.text is not None
    )
    data: dict[str, Any] = {
        "prefix": identifier,
        "name": tree_inner.findtext(f"{SCHEMA}repositoryName"),
        "description": tree_inner.findtext(f"{SCHEMA}description"),
        "homepage": tree_inner.findtext(f"{SCHEMA}repositoryURL"),
        "prefix_synonyms": [
            element.text.strip()
            for element in tree_inner.findall(f"{SCHEMA}additionalName")
            if element.text is not None
        ],
        "xrefs": dict(tup for tup in xrefs if tup),
    }

    license_element = tree_inner.find(f"{SCHEMA}databaseLicense/{SCHEMA}databaseLicenseName")
    if license_element is not None:
        data["license"] = License(name=license_element.text)

    return make_record(data)


def _clean_xref(xref: str) -> tuple[str, str] | None:
    for pp in [
        "FAIRsharing_DOI:10.25504/",
        "FAIRsharing_doi:10.25504/",
        "FAIRsharing_dOI:10.25504/",
        "FAIRsharing_doi:10.25504/",
        "FAIRSharing_doi:10.25504/",
        "FAIRsharing_doi;10.25504/",
        "FAIRsharing_doi: 10.25504/",
        "fairsharing_doi:10.25504/",
        "fairsharing_DOI:10.25504/",
        "FAIRsharin_doi:10.25504/",
        "FAIRsharing_doi.:10.25504/",
        "FAIRsharing_DOI: 10.25504/",
        "FAIRsharing_doi::10.25504/",
        "FAIRsharing_doi:10.24404/",
    ]:
        if xref.startswith(pp):
            return "fairsharing", xref.removeprefix(pp)

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
    """Aligner for the Registry of Research Data Repositories (re3data)."""

    key = "re3data"
    alt_key_match = "name"
    getter = get_re3data
    curation_header: ClassVar[Sequence[str]] = ("name", "homepage", "description")


if __name__ == "__main__":
    Re3dataAligner.cli()
