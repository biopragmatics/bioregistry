# -*- coding: utf-8 -*-

"""Align CHEMINF with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.cheminf import get_cheminf

__all__ = [
    "ChemInfAligner",
]


class ChemInfAligner(Aligner):
    """Aligner for the Chemical Information Ontology."""

    key = "cheminf"
    getter = get_cheminf
    curation_header = ("name", "description")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned CHEMINF registry entries."""
        return [
            external_entry["name"],
            external_entry["description"],
        ]


if __name__ == "__main__":
    ChemInfAligner.align()
