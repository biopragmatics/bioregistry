# -*- coding: utf-8 -*-

"""Scraper for FAIRsharing.

.. seealso:: https://beta.fairsharing.org/API_doc
"""

import json
import logging
import re
from pathlib import Path
from typing import Any, MutableMapping, Optional, Set

from bioregistry.constants import ORCID_PATTERN
from bioregistry.external.alignment_utils import Aligner
from bioregistry.license_standardizer import standardize_license
from bioregistry.utils import removeprefix, removesuffix

__all__ = [
    "get_fairsharing",
    "FairsharingAligner",
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


def get_fairsharing(
    *, force_download: bool = False, force_reload: bool = False, use_tqdm: bool = False
):
    """Get the FAIRsharing registry."""
    if PROCESSED_PATH.exists() and not force_download and not force_reload:
        with PROCESSED_PATH.open() as file:
            return json.load(file)

    from fairsharing_client import load_fairsharing

    data = load_fairsharing(force_download=force_download, use_tqdm=use_tqdm)
    rv = {}
    for prefix, record in data.items():
        new_record = _process_record(record)
        if new_record:
            rv[prefix] = new_record
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, ensure_ascii=False, sort_keys=True)
    return rv


KEEP = {
    "description",
    "name",
    "subjects",
    "user_defined_tags",
    "domains",
}


def _process_record(record: MutableMapping[str, Any]) -> Optional[MutableMapping[str, Any]]:
    if record.get("record_type") not in ALLOWED_TYPES:
        return None
    rv = {key: record[key] for key in KEEP if record[key]}

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
            rv["abbreviation"] = removesuffix(abbreviation, suf)

    metadata = record.get("metadata", {})

    url_for_logo = record.get("url_for_logo")
    if url_for_logo is not None:
        rv["logo"] = "https://api.fairsharing.org" + url_for_logo

    homepage = metadata.get("homepage")
    if homepage:
        rv["homepage"] = homepage

    rv["publications"] = list(
        filter(
            None,
            (_process_publication(publication) for publication in record.get("publications", [])),
        )
    )

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
            rv["twitter"] = removeprefix(support_link["url"], "https://twitter.com/")
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
            continue
        else:
            rv["license"] = license_standard

    rv = {k: v for k, v in rv.items() if k and v}
    return rv


#: Licenses that are one-off and don't need curating
SKIP_LICENSES: Set[str] = set()


def _process_publication(publication):
    rv = {}
    doi = publication.get("doi")
    if doi:
        doi = doi.rstrip(".").lower()
        doi = removeprefix(doi, "doi:")
        doi = removeprefix(doi, "https://doi.org/")
        if "/" not in doi:
            doi = None
        else:
            rv["doi"] = doi
    pubmed = publication.get("pubmed_id")
    if pubmed:
        rv["pubmed"] = str(pubmed)
    if not doi and not pubmed:
        return
    title = publication.get("title")
    if title:
        title = title.replace("  ", " ").rstrip(".")
        rv["title"] = title
    year = publication.get("year")
    if year:
        rv["year"] = int(year)
    return rv


class FairsharingAligner(Aligner):
    """Aligner for the FAIRsharing."""

    key = "fairsharing"
    alt_key_match = "abbreviation"
    skip_deprecated = True
    getter = get_fairsharing
    curation_header = ("abbreviation", "name", "description")


if __name__ == "__main__":
    FairsharingAligner.cli()
