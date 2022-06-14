# -*- coding: utf-8 -*-

"""Align the AberOWL with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.aberowl import get_aberowl

__all__ = [
    "AberOWLAligner",
]


class AberOWLAligner(Aligner):
    """Aligner for AberOWL."""

    key = "aberowl"
    getter = get_aberowl
    curation_header = ["name", "homepage", "description"]

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned registry entries."""
        return [
            external_entry["name"],
            external_entry.get("homepage", ""),
            external_entry.get("description", ""),
        ]


if __name__ == "__main__":
    AberOWLAligner.align()
