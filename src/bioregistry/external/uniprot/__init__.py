"""Download and parse the UniProt Cross-ref database."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

import requests

from bioregistry.alignment_model import Record, dump_records, load_processed
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner
from bioregistry.utils import removeprefix

__all__ = [
    "UniProtAligner",
    "get_uniprot",
]

logger = logging.getLogger(__name__)

#: Download URL for the UniProt registry
URL = "https://rest.uniprot.org/database/stream?format=json&query=*"
DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "uniprot.json"
PROCESSED_PATH = DIRECTORY / "processed.json"

#: resources with these UniProt prefixes don't exist anymore
skip_prefixes = {
    "UniPathway",  # doesn't exist anymore
    "BRENDA",  # has bad format string contains EC, UniProt, and taxon
    "eggNOG",  # not sure what this does
    "PlantReactome",  # incomprehensible URLs
    "Reactome",  # incomprehensible URLs
}


def get_uniprot(*, force_download: bool = True) -> dict[str, Record]:
    """Get the UniProt registry."""
    if PROCESSED_PATH.is_file() and not force_download:
        return load_processed(PROCESSED_PATH)

    RAW_PATH.write_text(
        json.dumps(
            requests.get(URL, timeout=30).json(), indent=2, sort_keys=True, ensure_ascii=False
        )
    )
    rv = {}
    for record in json.loads(RAW_PATH.read_text())["results"]:
        prefix = record.pop("id")
        if prefix in skip_prefixes:
            continue

        processed_record = _process_record(record)
        if processed_record is None:
            continue
        rv[prefix] = processed_record

    dump_records(rv, PROCESSED_PATH)
    return rv


def _process_record(record: dict[str, Any]) -> Record | None:
    rv = {
        "name": record.pop("name"),
        "abbreviation": record.pop("abbrev"),
        "homepage": record.pop("servers")[0],
        "category": record.pop("category"),
    }
    publication = {}
    doi: str | None = record.pop("doiId", None)
    if doi is not None:
        doi = doi.lower().rstrip(".")
        doi = removeprefix(doi, "doi:")
        doi = removeprefix(doi, "https://doi.org/")
        if "/" in doi:
            publication["doi"] = doi
    pubmed = record.pop("pubMedId", None)
    if pubmed:
        publication["pubmed"] = str(pubmed)
    if publication:
        rv["publications"] = [publication]

    del record["linkType"]
    del record["statistics"]
    rv = {k: v for k, v in rv.items() if k and v}

    value = record.pop("dbUrl")
    if "%s" in value and "%u" in value:
        logger.debug(f"has both formats: {value}")
        return None
    else:
        value = value.replace("%s", "$1").replace("%u", "$1")
        if "$1" in value:
            rv[URI_FORMAT_KEY] = value
        else:
            logger.debug("no annotation in %s", rv["prefix"])
    if record:
        logger.debug("forgot something: %s", record)
    return Record.model_validate(rv)


class UniProtAligner(Aligner):
    """Aligner for UniProt."""

    key = "uniprot"
    alt_key_match = "abbreviation"
    getter = get_uniprot
    curation_header: ClassVar[Sequence[str]] = ("abbreviation", "name", URI_FORMAT_KEY, "category")


if __name__ == "__main__":
    UniProtAligner.cli()
