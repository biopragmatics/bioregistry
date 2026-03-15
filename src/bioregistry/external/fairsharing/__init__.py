"""Scraper for FAIRsharing.

.. seealso::

    https://beta.fairsharing.org/API_doc
"""

from __future__ import annotations

import logging
import re
from collections.abc import MutableMapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

from bioregistry.alignment_model import (
    License,
    Publication,
    Record,
    dump_records,
    load_processed,
    make_record,
)
from bioregistry.constants import ORCID_PATTERN
from bioregistry.external.alignment_utils import Aligner, adapter
from bioregistry.license_standardizer import standardize_license
from bioregistry.utils import removeprefix, removesuffix

__all__ = [
    "FairsharingAligner",
    "get_fairsharing",
]

logger = logging.getLogger(__name__)

DIRECTORY = Path(__file__).parent.resolve()
PROCESSED_PATH = DIRECTORY / "processed.json"


ALLOWED_TYPES = {
    "terminology_artefact",
    "identifier_schema",
    # "knowledgebase",
    # "knowledgebase_and_repository",
    # "repository",
}

ORCID_RE = re.compile(ORCID_PATTERN)


@adapter
def get_fairsharing(
    *, force_download: bool = False, force_process: bool = False, use_tqdm: bool = True
) -> dict[str, Record]:
    """Get the FAIRsharing registry."""
    if PROCESSED_PATH.exists() and not force_download and not force_process:
        return load_processed(PROCESSED_PATH)

    from fairsharing_client import load_fairsharing

    data = load_fairsharing(force_download=force_download, use_tqdm=use_tqdm)
    rv = {
        prefix: record
        for prefix, raw_record in data.items()
        if (record := _process_record(raw_record)) is not None
    }
    dump_records(rv, PROCESSED_PATH)
    return rv


KEEP = {
    "description",
    "name",
}


def _process_record(record: MutableMapping[str, Any]) -> Record | None:
    if record.get("record_type") not in ALLOWED_TYPES:
        return None
    rv = {key: record[key] for key in KEEP if record[key]}

    for k in ["subjects", "user_defined_tags", "domains"]:
        if keywords := record.pop(k, None):
            rv.setdefault("keywords", []).extend(keywords)

    abbreviation = record.get("abbreviation")
    if abbreviation:
        for suf in [
            " CT",
            " CV",
            " Controlled Vocabulary",
            " Terminology",
            " Ontology",
            " Thesaurus",
            " Vocabulary",
            " Taxonomy",
        ]:
            rv["short_names"] = [removesuffix(abbreviation, suf)]

    metadata = record.get("metadata", {})

    url_for_logo = record.get("url_for_logo")
    if url_for_logo is not None:
        rv["logo"] = "https://api.fairsharing.org" + url_for_logo

    homepage = metadata.get("homepage")
    if homepage:
        rv["homepage"] = homepage

    if publications := record.pop("publications", []):
        rv["publications"] = [
            publication
            for publication_raw in publications
            if (publication := _process_publication(publication_raw))
        ]

    contacts = [
        {removeprefix(k, "contact_"): v for k, v in contact.items()}
        for contact in metadata.get("contacts", [])
        # make sure ORCID is available and valid
        if (orcid := contact.get("contact_orcid")) and ORCID_RE.match(orcid)
    ]
    for contact in contacts:
        contact["name"] = removeprefix(removeprefix(contact["name"], "Dr. "), "Dr ")
        if "orcid" in contact:
            contact["orcid"] = contact["orcid"].replace(" ", "")
    if contacts:
        rv["contact"] = contacts[0]

    for support_link in metadata.get("support_links", []):
        if support_link["type"] == "Twitter":
            pass
            # rv["twitter"] = removeprefix(support_link["url"], "https://twitter.com/")
        if support_link["type"] == "Github":
            rv["repository"] = support_link["url"]

    missed = set()
    for license_link in record.get("licence_links", []):
        url = license_link.get("licence_url")
        if not url:
            continue
        license_standard = standardize_license(url)
        if license_standard == url:
            if license_standard not in missed and license_standard not in SKIP_LICENSES:
                missed.add(license_standard)
                logger.debug("Need to curate license URL: %s", license_standard)
            rv["license"] = License(url=url)
        else:
            rv["license"] = License(name=license_standard, url=url)

    return make_record(rv)


#: Licenses that are one-off and don't need curating
SKIP_LICENSES: set[str] = set()


def _process_publication(data: dict[str, Any]) -> Publication | None:
    rv = {}
    if url := data.pop("url", None):
        rv["url"] = url
    if doi := data.pop("doi", None):
        doi = doi.rstrip(".").lower()
        doi = removeprefix(doi, "doi:")
        doi = removeprefix(doi, "https://doi.org/")
        if "/" not in doi:
            doi = None
        else:
            rv["doi"] = doi
    if pubmed := data.pop("pubmed_id", None):
        rv["pubmed"] = str(pubmed)
    if not doi and not pubmed:
        return None
    if title := data.pop("title", None):
        title = title.replace("  ", " ").rstrip(".")
        rv["title"] = title
    if year := data.pop("year", None):
        rv["year"] = int(year)
    return Publication.model_validate(rv)


class FairsharingAligner(Aligner):
    """Aligner for the FAIRsharing."""

    key = "fairsharing"
    alt_key_match = "short_names"
    skip_deprecated = True
    getter = get_fairsharing
    curation_header: ClassVar[Sequence[str]] = ("abbreviation", "name", "description")


if __name__ == "__main__":
    FairsharingAligner.cli()
