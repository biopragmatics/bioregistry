# -*- coding: utf-8 -*-

"""Download BioContext."""

import json
from pathlib import Path
from typing import Any, Dict, Mapping, Sequence

from pystow.utils import download

from bioregistry.constants import RAW_DIRECTORY, URI_FORMAT_KEY
from bioregistry.external.alignment_utils import Aligner

__all__ = [
    "get_biocontext",
    "BioContextAligner",
]

DIRECTORY = Path(__file__).parent.resolve()
RAW_PATH = RAW_DIRECTORY / "biocontext.json"
PROCESSED_PATH = DIRECTORY / "processed.json"
URL = "https://raw.githubusercontent.com/prefixcommons/biocontext/master/registry/commons_context.jsonld"
SKIP_PARTS = {"identifiers.org", "purl.obolibrary.org"}


def get_biocontext(force_download: bool = False) -> Mapping[str, Mapping[str, Any]]:
    """Get the BioContext context map.

    :param force_download: If true, forces download. If false and the file
        is already cached, reuses it.
    :returns: The biocontext data dictionary

    .. seealso:: https://github.com/prefixcommons/biocontext
    """
    if PROCESSED_PATH.exists() and not force_download:
        with PROCESSED_PATH.open() as file:
            return json.load(file)
    download(url=URL, path=RAW_PATH, force=force_download)
    with RAW_PATH.open() as file:
        data = json.load(file)
    rv = {
        prefix: {URI_FORMAT_KEY: f"{uri_prefix.strip()}$1"}
        for prefix, uri_prefix in data["@context"].items()
    }
    with PROCESSED_PATH.open("w") as file:
        json.dump(rv, file, indent=2, sort_keys=True)
    return rv


class BioContextAligner(Aligner):
    """Aligner for BioContext."""

    key = "biocontext"
    getter = get_biocontext
    curation_header = [URI_FORMAT_KEY]

    def get_skip(self) -> Mapping[str, str]:
        """Get entries for BioContext that should be skipped."""
        return {
            "fbql": "not a real resource, as far as I can tell",
        }

    def prepare_external(self, external_id: str, external_entry: dict[str, Any]) -> Dict[str, Any]:
        """Prepare BioContext data to be added to the BioContext for each BioPortal registry entry."""
        uri_format = external_entry[URI_FORMAT_KEY]
        if any(p in uri_format for p in SKIP_PARTS):
            return {}
        return {URI_FORMAT_KEY: uri_format}

    def get_curation_row(self, external_id: str, external_entry: dict[str, Any]) -> Sequence[str]:
        """Prepare curation rows for unaligned BioContext registry entries."""
        formatter = external_entry[URI_FORMAT_KEY]
        return [formatter]


if __name__ == "__main__":
    BioContextAligner.cli()
