# -*- coding: utf-8 -*-

"""Align Prefix Commons with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.prefixcommons import get_prefixcommons

__all__ = [
    "PrefixCommonsAligner",
]


class PrefixCommonsAligner(Aligner):
    """Aligner for Prefix Commons."""

    key = "prefixcommons"
    getter = get_prefixcommons
    curation_header = ("name", "description", "miriam", "bioportal")
    # TODO consider updating
    include_new = False

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned Prefix Commons registry entries."""
        return [
            external_entry["name"].strip(),
            external_entry.get("description", ""),
            external_entry.get("miriam", ""),
            external_entry.get("bioportal", ""),
        ]


if __name__ == "__main__":
    PrefixCommonsAligner.align()
