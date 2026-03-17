"""Download and parse the UniProt Cross-ref database."""

from __future__ import annotations

import json
import logging
from collections.abc import Sequence
from pathlib import Path
from typing import Any, ClassVar

from bioregistry.alignment_model import Record
from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, build_getter
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

# the field to use as the prefix in UniProt dblist records
PREFIX_FIELD = "abbrev"

#: resources with these UniProt prefixes don't exist anymore
UNIPROT_SKIP_PREFIXES = {
    "UniPathway",  # doesn't exist anymore
    "BRENDA",  # has bad format string contains EC, UniProt, and taxon
    "eggNOG",  # not sure what this does
    "PlantReactome",  # incomprehensible URLs
    "Reactome",  # incomprehensible URLs
    "GeneWiki",  # genewiki abbrev
}

HAS_BAD_URI = {
    "EnsemblFungi",  # ensembl.fungi
    "EnsemblBacteria",  # ensembl.bacteria
}


def process_uniprot_raw(path: Path) -> dict[str, Record]:
    """Process UniProt raw JSON."""
    rv = {}
    for record in json.loads(path.read_text())["results"]:
        prefix = record.pop(PREFIX_FIELD)
        if prefix in UNIPROT_SKIP_PREFIXES:
            continue
        if processed_record := _process_record(prefix, record):
            rv[prefix] = processed_record
    return rv


def _process_record(prefix: str, record: dict[str, Any]) -> Record | None:
    rv = {
        "name": record.pop("name"),
        "homepage": record.pop("servers")[0],
        "keywords": [record.pop("category")],
    }

    value = record.pop("dbUrl")
    if "%s" in value and "%u" in value:
        logger.debug("has both formats: %s", value)
        return None

    value = value.replace("%s", "$1").replace("%u", "$1")
    if "$1" in value and prefix not in HAS_BAD_URI:
        rv[URI_FORMAT_KEY] = value
    else:
        logger.debug("no annotation in %s", prefix)

    publication = {}
    if doi := record.pop("doiId", None):
        doi = doi.lower().rstrip(".")
        doi = removeprefix(doi, "doi:")
        doi = removeprefix(doi, "https://doi.org/")
        if "/" in doi:
            publication["doi"] = doi
    if pubmed := record.pop("pubMedId", None):
        publication["pubmed"] = str(pubmed)
    if publication:
        rv["publications"] = [publication]

    for key in ["id", "linkType", "statistics"]:
        del record[key]

    if record:
        logger.debug("forgot something: %s", record)
    return Record.model_validate(rv)


get_uniprot = build_getter(
    processed_path=PROCESSED_PATH,
    raw_path=RAW_PATH,
    url=URL,
    func=process_uniprot_raw,
)


class UniProtAligner(Aligner):
    """Aligner for UniProt."""

    key = "uniprot"
    getter = get_uniprot
    curation_header: ClassVar[Sequence[str]] = ("name", URI_FORMAT_KEY, "keywords")


if __name__ == "__main__":
    UniProtAligner.cli()
