# -*- coding: utf-8 -*-

"""Align CHEMINF with the Bioregistry."""

from typing import Mapping

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


if __name__ == "__main__":
    ChemInfAligner.cli()
