"""Download the Gene Ontology registry."""

import json
import logging
from collections.abc import Mapping, Sequence
from pathlib import Path
from typing import Any, ClassVar

import yaml
from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner, load_processed

__all__ = [
    "GoAligner",
    "get_go",
]

logger = logging.getLogger(__name__)

# Xrefs from GO that aren't generally useful
SKIP = {
    "TO_GIT",
    "OBO_SF_PO",
    "OBO_SF2_PO",
    "OBO_SF2_PECO",
    "PECO_GIT",
    "PO_GIT",
    "PSO_GIT",
    "EO_GIT",
}

# The key is redundant of the value
REDUNDANT = {
    "AspGD": "AspGD_LOCUS",
}

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "go.yml"
PROCESSED_PATH = DIRECTORY / "processed.json"
GO_URL = "https://raw.githubusercontent.com/geneontology/go-site/master/metadata/db-xrefs.yaml"
PROCESSING_GO_PATH = DIRECTORY / "processing_go.json"


def get_go(force_download: bool = False) -> dict[str, dict[str, Any]]:
    """Get the GO registry."""
    if PROCESSED_PATH.exists() and not force_download:
        return load_processed(PROCESSED_PATH)

    download(url=GO_URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        entries = yaml.full_load(file)
    entries = [
        entry
        for entry in entries
        if entry["database"] not in SKIP and entry["database"] not in REDUNDANT
    ]
    rv = {entry["database"]: entry for entry in entries}
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


class GoAligner(Aligner):
    """An aligner for the Gene Ontology (GO) registry."""

    key = "go"
    getter = get_go
    curation_header: ClassVar[Sequence[str]] = "name", "description"

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped GO identifiers."""
        with PROCESSING_GO_PATH.open() as file:
            j = json.load(file)
        return j["skip"]  # type:ignore

    def prepare_external(
        self, external_id: str, external_entry: Mapping[str, Any]
    ) -> dict[str, Any]:
        """Prepare GO data to be added to the bioregistry for each GO registry entry."""
        rv = {
            "name": external_entry["name"],
        }

        description = external_entry.get("description")
        if description:
            rv["description"] = description

        homepages = [
            homepage
            for homepage in external_entry.get("generic_urls", [])
            if not any(
                homepage.startswith(homepage_prefix)
                for homepage_prefix in [
                    "http://purl.obolibrary.org",
                ]
            )
        ]
        if len(homepages) > 1:
            logger.info(f"{external_id} multiple homepages {homepages}")
        if homepages:
            rv["homepage"] = homepages[0]

        entity_types = external_entry.get("entity_types", [])
        if len(entity_types) > 1:
            logger.info(f"{external_id} multiple entity types")
            # TODO handle
        elif len(entity_types) == 1:
            entity_type = entity_types[0]
            uri_format = entity_type.get("url_syntax")
            if uri_format and not any(
                uri_format.startswith(formatter_prefix)
                for formatter_prefix in [
                    "http://purl.obolibrary.org",
                    "https://purl.obolibrary.org",
                ]
            ):
                uri_format = uri_format.replace("[example_id]", "$1")
                rv[URI_FORMAT_KEY] = uri_format

        if "synonyms" in external_entry:
            rv["synonyms"] = external_entry["synonyms"]

        return rv


if __name__ == "__main__":
    GoAligner.cli()
