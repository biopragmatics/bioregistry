# -*- coding: utf-8 -*-

"""Download Biolink."""

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

import yaml
from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "get_biolink",
    "BiolinkAligner",
]

URL = "https://raw.githubusercontent.com/biolink/biolink-model/master/biolink-model.yaml"

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "biolink.yaml"
PROCESSED_PATH = DIRECTORY / "processed.json"

PROCESSING_BIOLINK_PATH = DIRECTORY / "processing_biolink.json"


def get_biolink(force_download: bool = False) -> dict[str, dict[str, str]]:
    """Get Biolink."""
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    download(url=URL, path=RAW_PATH, force=True)
    with RAW_PATH.open() as file:
        data = yaml.safe_load(file)
    rv = {
        prefix: {URI_FORMAT_KEY: f"{uri_prefix}$1"}
        for prefix, uri_prefix in data["prefixes"].items()
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


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

    def prepare_external(self, external_id: str, external_entry) -> Dict[str, Any]:
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
