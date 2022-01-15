# -*- coding: utf-8 -*-

"""Align the Prefix Commons with the Bioregistry."""

from typing import Any, Dict, Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.prefix_commons import get_prefix_commons

__all__ = [
    "PrefixCommonsAligner",
]


class PrefixCommonsAligner(Aligner):
    """Aligner for Prefix Commons."""

    key = "prefixcommons"
    getter = get_prefix_commons
    curation_header = [URI_FORMAT_KEY, "identifiers", "purl"]

    def get_skip(self) -> Mapping[str, str]:
        """Get entries for prefix commons that should be skipped."""
        return {
            "fbql": "not a real resource, as far as I can tell",
        }

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare Prefix Commons data to be added to the Prefix Commons for each BioPortal registry entry."""
        uri_format = external_entry[URI_FORMAT_KEY].strip()
        return {
            URI_FORMAT_KEY: uri_format,
            "is_identifiers": uri_format.startswith("http://identifiers.org"),
            "is_obo": uri_format.startswith("http://purl.obolibrary.org"),
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Prefix Commons registry entries."""
        formatter = external_entry[URI_FORMAT_KEY]
        return [
            formatter,
            formatter.startswith("http://identifiers.org"),
            formatter.startswith("http://purl.obolibrary.org"),
        ]


if __name__ == "__main__":
    PrefixCommonsAligner.align()
