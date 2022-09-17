# -*- coding: utf-8 -*-

"""Align CHEMINF with the Bioregistry."""

from typing import Mapping, Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.cheminf import get_cheminf

__all__ = [
    "ChemInfAligner",
]

SKIP = {
    "000467": "Not enough information available on this term.",
    "000234": "PubChem Conformer isn't actually an identifier, just a part of PubChem Compound database",
    "000303": "Double mapping onto `genbank`",
}


class ChemInfAligner(Aligner):
    """Aligner for the Chemical Information Ontology."""

    key = "cheminf"
    getter = get_cheminf
    curation_header = ("name", "description")

    def get_skip(self) -> Mapping[str, str]:
        """Get the skipped identifiers."""
        return SKIP

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned CHEMINF registry entries."""
        return [
            external_entry["name"],
            external_entry.get("description") or "",
        ]


if __name__ == "__main__":
    ChemInfAligner.align()
