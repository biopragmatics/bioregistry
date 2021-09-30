# -*- coding: utf-8 -*-

"""Align MIRIAM with the Bioregistry."""

from typing import Sequence

from bioregistry.align.utils import Aligner
from bioregistry.external.miriam import get_miriam

__all__ = [
    "MiriamAligner",
]


class MiriamAligner(Aligner):
    """Aligner for the MIRIAM registry."""

    key = "miriam"
    getter = get_miriam
    curation_header = ("deprecated", "name", "description")
    include_new = True

    def get_curation_row(self, external_id, external_entry) -> Sequence[str]:
        """Prepare curation rows for unaligned MIRIAM registry entries."""
        return [
            external_entry["deprecated"],
            external_entry["name"].strip(),
            external_entry.get("description", "").strip(),
        ]


if __name__ == "__main__":
    MiriamAligner.align()
