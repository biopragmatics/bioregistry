# -*- coding: utf-8 -*-

"""Align FAIRsharing with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.fairsharing import get_fairsharing

__all__ = [
    "FairsharingAligner",
]


class FairsharingAligner(Aligner):
    """Aligner for the FAIRsharing."""

    key = "fairsharing"
    alt_key_match = "abbreviation"
    skip_deprecated = True
    getter = get_fairsharing
    curation_header = ("abbreviation", "name", "description")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["name"],
            external_entry["abbreviation"],
            external_entry["description"],
        ]


if __name__ == "__main__":
    FairsharingAligner.align()
