# -*- coding: utf-8 -*-

"""Align the Biolink with the Bioregistry."""

import json
from typing import Any, Dict, Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.constants import DATA_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.biolink import get_biolink

__all__ = [
    "BiolinkAligner",
]

PROCESSING_BIOLINK_PATH = DATA_DIRECTORY / "processing_biolink.json"


class BiolinkAligner(Aligner):
    """Aligner for Biolink."""

    key = "biolink"
    getter = get_biolink
    curation_header = [URI_FORMAT_KEY, "identifiers", "purl"]

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped Biolink identifiers."""
        with PROCESSING_BIOLINK_PATH.open() as file:
            j = json.load(file)
        return {entry["prefix"]: entry["reason"] for entry in j["skip"]}

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare Biolink data to be added to the Biolink for each BioPortal registry entry."""
        uri_format = external_entry[URI_FORMAT_KEY]
        return {
            URI_FORMAT_KEY: uri_format,
            "is_identifiers": uri_format.startswith("http://identifiers.org"),
            "is_obo": uri_format.startswith("http://purl.obolibrary.org"),
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Biolink registry entries."""
        uri_format = external_entry[URI_FORMAT_KEY]
        return [
            uri_format,
            uri_format.startswith("http://identifiers.org"),
            uri_format.startswith("http://purl.obolibrary.org"),
        ]


if __name__ == "__main__":
    BiolinkAligner.cli()
