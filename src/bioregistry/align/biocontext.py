# -*- coding: utf-8 -*-

"""Align the BioContext with the Bioregistry."""

from typing import Any, Dict, Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.biocontext import get_biocontext

__all__ = [
    "BioContextAligner",
]

SKIP_PARTS = {"identifiers.org", "purl.obolibrary.org"}


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

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare BioContext data to be added to the BioContext for each BioPortal registry entry."""
        uri_format = external_entry[URI_FORMAT_KEY]
        if any(p in uri_format for p in SKIP_PARTS):
            return {}
        return {URI_FORMAT_KEY: uri_format}

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioContext registry entries."""
        formatter = external_entry[URI_FORMAT_KEY]
        return [formatter]


if __name__ == "__main__":
    BioContextAligner.cli()
