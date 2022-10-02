# -*- coding: utf-8 -*-

"""Align the GO with the Bioregistry."""

import json
import logging
from typing import Any, Dict, Mapping

from bioregistry.align.utils import Aligner
from bioregistry.constants import DATA_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.go import get_go

__all__ = [
    "GoAligner",
]

logger = logging.getLogger(__name__)

PROCESSING_GO_PATH = DATA_DIRECTORY / "processing_go.json"


class GoAligner(Aligner):
    """An aligner for the Gene Ontology (GO) registry."""

    key = "go"
    getter = get_go
    curation_header = "name", "description"

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped GO identifiers."""
        with PROCESSING_GO_PATH.open() as file:
            j = json.load(file)
        return j["skip"]

    def prepare_external(
        self, external_id: str, external_entry: Mapping[str, Any]
    ) -> Dict[str, Any]:
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
    GoAligner.align()
