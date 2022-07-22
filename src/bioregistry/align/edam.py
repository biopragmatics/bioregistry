# -*- coding: utf-8 -*-

"""Align EDAM with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.edam import get_edam

__all__ = [
    "EDAMAligner",
]


class EDAMAligner(Aligner):
    """Aligner for the EDAM ontology."""

    key = "edam"
    getter = get_edam
    curation_header = ("name", "description")
    # FIXME remove this when out of canada and back on consistent wifi
    getter_kwargs = {"force_download": False}

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned EDAM ontology classes."""
        return [
            external_entry["name"],
            external_entry["description"],
        ]


if __name__ == "__main__":
    EDAMAligner.align()
