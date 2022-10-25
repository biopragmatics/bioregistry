# -*- coding: utf-8 -*-

"""Align Prefix Commons with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.prefixcommons import get_prefixcommons

__all__ = [
    "PrefixCommonsAligner",
]

SKIP = {
    "redidb": "Website is dead",
    "trnadbce": "Website is password protected",
    "pogs_plantrbp": "Website is dead",
}


class PrefixCommonsAligner(Aligner):
    """Aligner for Prefix Commons."""

    key = "prefixcommons"
    getter = get_prefixcommons
    curation_header = (
        "name",
        "synonyms",
        "description",
        "example",
        "pattern",
        "uri_format",
    )
    alt_keys_match = "synonyms"
    # TODO consider updating
    include_new = False

    def get_skip(self) -> Mapping[str, str]:
        """Get skip prefixes."""
        return SKIP

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Prefix Commons registry entries."""
        return [
            external_entry["name"],
            ", ".join(external_entry.get("synonyms", [])),
            external_entry.get("description", "").replace('"', ""),
            external_entry.get("example", ""),
            external_entry.get("pattern", ""),
            external_entry.get("uri_format", ""),
        ]


if __name__ == "__main__":
    PrefixCommonsAligner.align(force_download=False)
