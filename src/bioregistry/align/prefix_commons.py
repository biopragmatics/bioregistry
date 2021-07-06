# -*- coding: utf-8 -*-

"""Align the Prefix Commons with the Bioregistry."""

from typing import Any, Dict, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.prefix_commons import get_prefix_commons

__all__ = [
    "PrefixCommonsAligner",
]


class PrefixCommonsAligner(Aligner):
    """Aligner for Prefix Commons."""

    key = "prefixcommons"
    getter = get_prefix_commons
    curation_header = ["formatter", "identifiers", "purl"]

    def prepare_external(self, external_id, external_entry) -> Dict[str, Any]:
        """Prepare Prefix Commons data to be added to the Prefix Commons for each BioPortal registry entry."""
        formatter = external_entry["formatter"].strip()
        return {
            "formatter": formatter,
            "is_identifiers": formatter.startswith("http://identifiers.org"),
            "is_obo": formatter.startswith("http://purl.obolibrary.org"),
        }

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Prefix Commons registry entries."""
        formatter = external_entry["formatter"].strip()
        return [
            formatter,
            formatter.startswith("http://identifiers.org"),
            formatter.startswith("http://purl.obolibrary.org"),
        ]


if __name__ == "__main__":
    PrefixCommonsAligner.align()
