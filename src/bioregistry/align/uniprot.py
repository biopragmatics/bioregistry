# -*- coding: utf-8 -*-

"""Align the UniProt with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.constants import URI_FORMAT_KEY
from bioregistry.external.uniprot import get_uniprot

__all__ = [
    "UniProtAligner",
]


class UniProtAligner(Aligner):
    """Aligner for UniProt."""

    key = "uniprot"
    getter = get_uniprot
    curation_header = ("id", "name", URI_FORMAT_KEY, "category")

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned BioPortal registry entries."""
        return [
            external_entry["identifier"],
            external_entry["name"],
            external_entry.get(URI_FORMAT_KEY),
            external_entry.get("category"),
        ]


if __name__ == "__main__":
    UniProtAligner.align()
